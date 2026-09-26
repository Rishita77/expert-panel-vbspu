from django.utils.translation import gettext_lazy
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.access import permitted, require_role, roles_for
from apps.accounts.models import Role
from apps.audit.services import record
from apps.cases.models import RequestDraft
from apps.cases.services import EditConflict

from .engine import demonstration
from .forms import (
    AssessmentForm,
    FinalSelectionForm,
    GenerateForm,
    LetterPrepareForm,
    LetterReviewForm,
    PanelChangeStartForm,
    PanelChangeSubmitForm,
    ReviewForm,
)
from .models import (
    AllocationRun,
    Assessment,
    FinalSelection,
    LetterEvent,
    LetterRevision,
    PanelChange,
)
from .policies import POLICIES
from .services import (
    _current_panel_members,
    approve_letter,
    assess,
    confirm_panel_change,
    create_cancellation_change,
    create_final_selection,
    create_letter,
    create_replacement_change,
    generate,
    lock_final_selection,
    return_letter,
    return_panel_change,
    save_final_selection,
    submit_letter,
    submit_panel_change,
)


@permitted(Role.VC)
@require_http_methods(["GET", "POST"])
def workbench(request, pk):
    case = get_object_or_404(RequestDraft, pk=pk)
    generation = GenerateForm(initial={"revision": case.revision})
    errors = []
    status = 200
    roles = roles_for(request.user)
    can_vc = bool(roles & {Role.VC, Role.ADMIN})
    if request.method == "POST":
        action = request.POST.get("action")
        bound = GenerateForm(request.POST)
        try:
            if action != "generate":
                raise ValidationError(gettext_lazy("अमान्य कार्य।"))
            if bound.is_valid():
                data = bound.cleaned_data
                require_role(request.user, Role.VC)
                run = generate(request.user, pk, data["revision"])
                return redirect("allocation_run", pk=run.pk)
            status = 400
        except (ValidationError, EditConflict) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            status = 409 if isinstance(exc, EditConflict) else 400
        generation = bound
    return render(
        request,
        "nominations/workbench.html",
        {
            "case": case,
            "generation": generation,
            "errors": errors,
            "today": timezone.localdate(),
            "runs": Paginator(AllocationRun.objects.filter(request=case), 15).get_page(
                request.GET.get("page")
            ),
            "can_vc": can_vc,
        },
        status=status,
    )


@permitted(Role.VC)
@require_http_methods(["GET", "POST"])
def run_detail(request, pk):
    run = get_object_or_404(AllocationRun.objects.select_related("request"), pk=pk)
    roles = roles_for(request.user)
    can_vc = bool(roles & {Role.VC, Role.ADMIN})
    errors, status = [], 200
    seats = run.snapshot.get("seats", [])
    seat_ids = {item["id"] for item in seats}
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "verify":
                form = AssessmentForm(request.POST)
                if not form.is_valid():
                    errors = [message for values in form.errors.values() for message in values]
                    status = 400
                elif str(form.cleaned_data["expert"].pk) not in seat_ids:
                    raise ValidationError(gettext_lazy("केवल प्रस्तावित पैनल सदस्य का सत्यापन दर्ज किया जा सकता है।"))
                else:
                    assess(
                        request.user,
                        run.request_id,
                        form.cleaned_data["expert"].pk,
                        form.cleaned_data,
                        form.cleaned_data["revision"],
                        allocation_date=run.allocation_date,
                    )
                    return redirect("allocation_run", pk=run.pk)
            elif action == "regenerate":
                revision = int(request.POST["revision"])
                new_run = generate(request.user, run.request_id, revision)
                return redirect("allocation_run", pk=new_run.pk)
            else:
                raise ValidationError(gettext_lazy("अमान्य कार्य।"))
        except (ValidationError, EditConflict, KeyError, ValueError) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            status = 409 if isinstance(exc, EditConflict) else 400
    assessments = {}
    for assessment in Assessment.objects.filter(
        request_id=run.request_id,
        request_revision=run.request_revision,
        allocation_date=run.allocation_date,
        expert_id__in=seat_ids,
    ).order_by("-recorded_at"):
        assessments.setdefault(str(assessment.expert_id), assessment)
    evidence = {
        (item["expert"], item["role"]): item for item in run.snapshot.get("candidate_evidence", [])
    }
    member_rows = []
    for seat in seats:
        facts = evidence.get((seat["id"], seat["role"]), {})
        assessment = assessments.get(seat["id"])
        member_rows.append(
            {
                "seat": seat,
                "institution": (facts.get("home") or {}).get("institution_name", "—"),
                "designation": (facts.get("home") or {}).get("academic_designation", "—"),
                "assessment": assessment,
                "form": AssessmentForm(
                    initial={
                        "revision": run.request_revision,
                        "expert": seat["id"],
                        "status": assessment.status if assessment else "available",
                        "conflict": "yes" if assessment and assessment.conflict else "no",
                        "verifier": assessment.verifier if assessment else "",
                        "reason": assessment.reason if assessment else "",
                    }
                ),
            }
        )
    return render(
        request,
        "nominations/result.html",
        {
            "result": run.snapshot,
            "run": run,
            "stale": run.request_revision != run.request.revision,
            "selection": getattr(run, "finalselection", None),
            "can_vc": can_vc,
            "can_reviewer": can_vc,
            "member_rows": member_rows,
            "errors": errors,
        },
        status=status,
    )


@permitted(Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def start_offer_letter(request, pk):
    run = get_object_or_404(AllocationRun.objects.select_related("request"), pk=pk)
    return _start_letter(request, "offer", run, "allocation_run", gettext_lazy("प्रस्तावित पैनल पत्र"))


@permitted(Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def start_final_letter(request, pk):
    selection = get_object_or_404(FinalSelection.objects.select_related("request"), pk=pk)
    return _start_letter(request, "final", selection, "final_selection", gettext_lazy("अंतिम चयन पत्र"))


@permitted(Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def start_change_letter(request, pk):
    change = get_object_or_404(PanelChange.objects.select_related("selection__request"), pk=pk)
    return _start_letter(
        request, change.change_type, change, "panel_change", change.get_change_type_display()
    )


def _start_letter(request, kind, source, source_view, title):
    errors, status = [], 200
    form = LetterPrepareForm(initial={"letter_date": timezone.localdate()})
    if request.method == "POST":
        form = LetterPrepareForm(request.POST)
        if form.is_valid():
            try:
                revision = create_letter(request.user, kind, source.pk, **form.cleaned_data)
                return redirect("letter", pk=revision.pk)
            except (ValidationError, EditConflict) as exc:
                errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
                status = 409 if isinstance(exc, EditConflict) else 400
        else:
            status = 400
    return render(
        request,
        "nominations/letter_start.html",
        {
            "source": source,
            "source_view": source_view,
            "title": title,
            "form": form,
            "errors": errors,
        },
        status=status,
    )


@permitted(Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def letter(request, pk):
    revision = get_object_or_404(
        LetterRevision.objects.select_related("letter", "letter__request"), pk=pk
    )
    roles = roles_for(request.user)
    can_process = False
    can_reviewer = bool(roles & {Role.REVIEWER, Role.VC, Role.ADMIN})
    can_vc = bool(roles & {Role.VC, Role.ADMIN})
    errors, status = [], 200
    form = LetterReviewForm(initial={"revision": revision.revision})
    if request.method == "POST":
        action = request.POST.get("action")
        form = LetterReviewForm(request.POST)
        try:
            if not form.is_valid():
                status = 400
            elif action == "submit":
                revision = submit_letter(request.user, pk, form.cleaned_data["revision"])
                return redirect("letter", pk=revision.pk)
            elif action == "return":
                require_role(request.user, Role.VC)
                revision = return_letter(
                    request.user, pk, form.cleaned_data["revision"], form.cleaned_data["reason"]
                )
                return redirect("letter", pk=revision.pk)
            elif action == "approve":
                require_role(request.user, Role.VC)
                revision = approve_letter(request.user, pk, form.cleaned_data["revision"])
                return redirect("letter", pk=revision.pk)
            else:
                raise ValidationError(gettext_lazy("अमान्य कार्य।"))
        except (ValidationError, EditConflict) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            status = 409 if isinstance(exc, EditConflict) else 400
    revision.refresh_from_db()
    return render(
        request,
        "nominations/letter.html",
        {
            "revision": revision,
            "form": form,
            "errors": errors,
            "can_process": can_process,
            "can_reviewer": can_reviewer,
            "can_vc": can_vc,
            "events": revision.events.select_related("actor"),
        },
        status=status,
    )


@permitted(Role.REVIEWER, Role.VC)
def document_queue(request):
    state = request.GET.get("state", "").strip()
    revisions = LetterRevision.objects.select_related(
        "letter", "letter__request", "created_by", "approved_by"
    ).order_by("state", "-created_at")
    if state in LetterRevision.State.values:
        revisions = revisions.filter(state=state)
    return render(
        request,
        "nominations/document_queue.html",
        {
            "revisions": Paginator(revisions, 30).get_page(request.GET.get("page")),
            "selected_state": state,
            "states": LetterRevision.State.choices,
        },
    )


@permitted(Role.PROCESSOR, Role.REVIEWER, Role.VC)
def letter_download(request, pk):
    revision = get_object_or_404(
        LetterRevision.objects.select_related("letter", "source_selection"),
        pk=pk,
        state=LetterRevision.State.APPROVED,
    )
    roles = roles_for(request.user)
    is_poc_only = Role.PROCESSOR in roles and not roles & {Role.REVIEWER, Role.VC, Role.ADMIN}
    if is_poc_only and (
        revision.letter.kind != "final"
        or not revision.source_selection_id
        or revision.source_selection.state != FinalSelection.State.LOCKED
    ):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied(gettext_lazy("POC केवल जारी अंतिम चयन पत्र डाउनलोड कर सकता है।"))
    path = Path(settings.PRIVATE_DOCUMENT_ROOT) / revision.pdf_key
    if not revision.pdf_key or not path.is_file():
        raise Http404(gettext_lazy("पत्र PDF उपलब्ध नहीं है।"))
    LetterEvent.objects.create(revision=revision, action="downloaded", actor=request.user)
    record(request.user, "letter.downloaded", revision)
    return FileResponse(
        path.open("rb"), as_attachment=True, filename=f"{revision.letter.reference}.pdf"
    )


@permitted(Role.VC)
@require_http_methods(["POST"])
def start_final_selection(request, pk):
    try:
        selection = create_final_selection(request.user, pk)
        return redirect("final_selection", pk=selection.pk)
    except (ValidationError, EditConflict) as exc:
        return render(
            request,
            "nominations/blocked.html",
            {"errors": exc.messages if isinstance(exc, ValidationError) else [str(exc)]},
            status=409,
        )


@permitted(Role.PROCESSOR, Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def final_selection(request, pk):
    selection = get_object_or_404(
        FinalSelection.objects.select_related("request", "source_run"), pk=pk
    )
    roles = roles_for(request.user)
    is_poc_only = Role.PROCESSOR in roles and not roles & {Role.REVIEWER, Role.VC, Role.ADMIN}
    if is_poc_only and selection.state != FinalSelection.State.LOCKED:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied(gettext_lazy("प्रस्तावित पैनल केवल रजिस्ट्रार, VC और प्रशासक देख सकते हैं।"))
    can_process = False
    can_reviewer = bool(roles & {Role.REVIEWER, Role.VC, Role.ADMIN})
    can_vc = bool(roles & {Role.VC, Role.ADMIN})
    errors, status = [], 200
    selection_form = FinalSelectionForm(
        initial={
            "revision": selection.revision,
            "vc_reference": selection.vc_reference,
        }
    )
    review_form = ReviewForm(initial={"revision": selection.revision})
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "save":
                if not can_vc:
                    require_role(request.user, Role.VC)
                selection_form = FinalSelectionForm(request.POST)
                if not selection_form.is_valid():
                    status = 400
                else:
                    selection = save_final_selection(
                        request.user,
                        pk,
                        selection_form.cleaned_data,
                        request.POST.getlist("members"),
                    )
                    return redirect("final_selection", pk=selection.pk)
            elif action == "lock":
                if not can_vc:
                    require_role(request.user, Role.VC)
                review_form = ReviewForm(request.POST)
                if not review_form.is_valid():
                    status = 400
                else:
                    selection = lock_final_selection(
                        request.user,
                        pk,
                        review_form.cleaned_data["revision"],
                        review_form.cleaned_data["reason"],
                    )
                    return redirect("final_selection", pk=selection.pk)
            else:
                raise ValidationError(gettext_lazy("अमान्य कार्य।"))
        except (ValidationError, EditConflict, KeyError) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            status = 409 if isinstance(exc, EditConflict) else 400
    selection.refresh_from_db()
    return render(
        request,
        "nominations/final_selection.html",
        {
            "selection": selection,
            "members": selection.members.select_related("expert"),
            "selection_form": selection_form,
            "review_form": review_form,
            "errors": errors,
            "can_process": can_process,
            "can_reviewer": can_reviewer,
            "can_vc": can_vc,
            "changes": selection.changes.select_related("outgoing_expert", "replacement_expert"),
        },
        status=status,
    )


@permitted(Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def panel_change_start(request, pk):
    selection = get_object_or_404(FinalSelection, pk=pk, state=FinalSelection.State.LOCKED)
    current = _current_panel_members(selection)
    form = PanelChangeStartForm(experts=[member["expert_id"] for member in current.values()])
    errors, status = [], 200
    if request.method == "POST":
        require_role(request.user, Role.REVIEWER, Role.VC)
        form = PanelChangeStartForm(
            request.POST, experts=[member["expert_id"] for member in current.values()]
        )
        try:
            if not form.is_valid():
                status = 400
            elif request.POST.get("action") == "replacement":
                change = create_replacement_change(
                    request.user,
                    selection.pk,
                    form.cleaned_data["outgoing_expert"].pk,
                    form.cleaned_data["reason"],
                    form.cleaned_data["verifier"],
                )
                return redirect("panel_change", pk=change.pk)
            elif request.POST.get("action") == "cancellation":
                change = create_cancellation_change(
                    request.user,
                    selection.pk,
                    form.cleaned_data["reason"],
                    form.cleaned_data["verifier"],
                    form.cleaned_data["work_not_occurred"],
                )
                return redirect("panel_change", pk=change.pk)
            else:
                raise ValidationError(gettext_lazy("अमान्य कार्य।"))
        except (ValidationError, EditConflict) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            status = 409 if isinstance(exc, EditConflict) else 400
    return render(
        request,
        "nominations/panel_change_start.html",
        {"selection": selection, "form": form, "errors": errors},
        status=status,
    )


@permitted(Role.REVIEWER, Role.VC)
@require_http_methods(["GET", "POST"])
def panel_change(request, pk):
    change = get_object_or_404(
        PanelChange.objects.select_related(
            "selection", "outgoing_expert", "replacement_expert", "source_run"
        ),
        pk=pk,
    )
    roles = roles_for(request.user)
    can_process = False
    can_reviewer = bool(roles & {Role.REVIEWER, Role.VC, Role.ADMIN})
    can_vc = bool(roles & {Role.VC, Role.ADMIN})
    errors, status = [], 200
    submit_form = PanelChangeSubmitForm(initial={"revision": change.revision})
    review_form = ReviewForm(initial={"revision": change.revision})
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "submit":
                require_role(request.user, Role.REVIEWER, Role.VC)
                submit_form = PanelChangeSubmitForm(request.POST)
                if not submit_form.is_valid():
                    status = 400
                else:
                    change = submit_panel_change(
                        request.user,
                        pk,
                        submit_form.cleaned_data["revision"],
                        submit_form.cleaned_data,
                    )
                    return redirect("panel_change", pk=change.pk)
            elif action == "return":
                require_role(request.user, Role.VC)
                review_form = ReviewForm(request.POST)
                if not review_form.is_valid():
                    status = 400
                else:
                    change = return_panel_change(
                        request.user,
                        pk,
                        review_form.cleaned_data["revision"],
                        review_form.cleaned_data["reason"],
                    )
                    return redirect("panel_change", pk=change.pk)
            elif action == "confirm":
                require_role(request.user, Role.VC)
                review_form = ReviewForm(request.POST)
                if not review_form.is_valid():
                    status = 400
                else:
                    change = confirm_panel_change(
                        request.user,
                        pk,
                        review_form.cleaned_data["revision"],
                        review_form.cleaned_data["reason"],
                    )
                    return redirect("panel_change", pk=change.pk)
            else:
                raise ValidationError(gettext_lazy("अमान्य कार्य।"))
        except (ValidationError, EditConflict) as exc:
            errors = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
            status = 409 if isinstance(exc, EditConflict) else 400
    change.refresh_from_db()
    return render(
        request,
        "nominations/panel_change.html",
        {
            "change": change,
            "errors": errors,
            "submit_form": submit_form,
            "review_form": review_form,
            "can_process": can_process,
            "can_reviewer": can_reviewer,
            "can_vc": can_vc,
            "events": change.review_events.select_related("actor"),
        },
        status=status,
    )


@permitted(Role.PROCESSOR, Role.REVIEWER)
def demo(request):
    appointment = request.GET.get("appointment", "principal")
    scenario = request.GET.get("scenario", "standard")
    if appointment not in POLICIES or scenario not in {"standard", "fairness", "shortage"}:
        raise Http404("Unknown demonstration scenario")
    return render(
        request,
        "nominations/result.html",
        {"result": demonstration(timezone.localdate(), appointment, scenario)},
    )
