from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.access import require_role
from apps.accounts.models import Role, StaffUser
from apps.accounts.services import save_staff
from apps.audit.models import AuditEvent
from apps.audit.presentation import present
from apps.institutions.models import Institution, Subject

from .forms import DraftForm, InstitutionForm, RequestReturnForm, StaffForm, SubjectForm
from .models import RequestDraft
from .services import EditConflict, approve_review, return_request, save_record, submit_request

REGISTRY = {
    "institutions": (Institution, InstitutionForm, _("संस्थाएँ"), "master"),
    "subjects": (Subject, SubjectForm, _("विषय"), "master"),
    "requests": (RequestDraft, DraftForm, _("अनुरोध प्रारूप"), "processor"),
    "staff": (StaffUser, StaffForm, _("कर्मचारी खाते"), "admin"),
}


def spec(kind):
    if kind not in REGISTRY:
        from django.http import Http404

        raise Http404
    return REGISTRY[kind]


def read_permission(user, kind):
    if kind == "staff":
        require_role(user, Role.ADMIN)
    elif kind == "requests":
        require_role(user, Role.PROCESSOR, Role.REVIEWER, Role.VC)
    else:
        require_role(user, *Role.values)


@login_required
@require_GET
def home(request):
    return render(request, "office/home.html")


@login_required
@require_GET
def listing(request, kind):
    model, _, title, write_role = spec(kind)
    read_permission(request.user, kind)
    rows = model.objects.all()
    if kind == "requests":
        rows = rows.select_related("institution", "subject", "updated_by")
    query = request.GET.get("q", "").strip()[:200]
    if query:
        if kind == "requests":
            rows = rows.filter(
                Q(institution__name__icontains=query)
                | Q(advertisement__icontains=query)
                | Q(subject__name__icontains=query)
            )
        elif kind == "staff":
            rows = rows.filter(Q(full_name__icontains=query) | Q(username__icontains=query))
        else:
            rows = rows.filter(Q(name__icontains=query) | Q(official_code__icontains=query))
    if kind == "staff":
        rows = rows.order_by("username")
    from apps.accounts.access import roles_for

    return render(
        request,
        "office/list.html",
        {
            "title": title,
            "kind": kind,
            "query": query,
            "page": Paginator(rows, 25).get_page(request.GET.get("page")),
            "can_write": write_role in roles_for(request.user)
            or Role.ADMIN in roles_for(request.user),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, kind, pk=None):
    model, form_class, title, write_role = spec(kind)
    require_role(request.user, write_role)
    if kind == "staff" and pk == request.user.pk:
        raise PermissionDenied("अपने खाते की अनुमतियाँ यहाँ नहीं बदल सकते।")
    obj = get_object_or_404(model, pk=pk) if pk else model()
    form = form_class(request.POST if request.method == "POST" else None, instance=obj)
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            if kind == "staff":
                data = form.cleaned_data
                saved = save_staff(
                    request.user,
                    data,
                    data["roles"],
                data.get("reason", _("नया कर्मचारी खाता बनाया गया")),
                    pk,
                )
            else:
                saved = save_record(
                    request.user, model, form.cleaned_data, form.cleaned_data["revision"], pk
                )
            return redirect("office_detail", kind=kind, pk=saved.pk)
        except EditConflict as exc:
            form.add_error(None, exc)
            status = 409
        except ValidationError as exc:
            for message in exc.messages:
                form.add_error(None, message)
        except IntegrityError:
            form.add_error(None, _("रिकॉर्ड बदल गया या यह पहचान पहले से मौजूद है। जाँचकर पुनः सहेजें।"))
            status = 409
    return render(
        request,
        "office/form.html",
        {
            "form": form,
            "title": title,
            "kind": kind,
            "record": obj if pk else None,
            "is_edit": bool(pk),
        },
        status=status,
    )


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, kind, pk):
    model, form_class, title, write_role = spec(kind)
    read_permission(request.user, kind)
    obj = get_object_or_404(model, pk=pk)
    if kind == "requests" and request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "submit":
                submit_request(request.user, obj.pk, int(request.POST["revision"]))
            elif action == "review_accept":
                approve_review(request.user, obj.pk, int(request.POST["revision"]))
            elif action == "return":
                return_form = RequestReturnForm(request.POST)
                if not return_form.is_valid():
                    raise ValidationError(return_form.errors.as_text())
                return_request(
                    request.user,
                    obj.pk,
                    return_form.cleaned_data["revision"],
                    return_form.cleaned_data["reason"],
                )
            else:
                raise ValidationError("अमान्य कार्य।")
            return redirect("office_detail", kind=kind, pk=obj.pk)
        except (ValidationError, EditConflict, ValueError) as exc:
            error = exc.messages if isinstance(exc, ValidationError) else [str(exc)]
        else:
            error = []
    else:
        error = []
    form = form_class(instance=obj)
    rows = []
    for name, field in form.fields.items():
        if name not in {f.name for f in model._meta.fields}:
            continue
        value = getattr(obj, name)
        if isinstance(value, bool):
            value = _("हाँ") if value else _("नहीं")
        if value is None or value == "":
            value = "—"
        display = getattr(obj, f"get_{name}_display", None)
        rows.append((field.label, display() if display else value))
    if kind == "staff":
        rows.append(
            (
                _("अनुमतियाँ"),
                ", ".join(
                    a.get_role_display()
                    for a in obj.role_assignments.filter(revoked_at__isnull=True)
                )
                or "—",
            )
        )
        if not obj.has_usable_password():
            rows.append((_("प्रमाण-पत्र स्थिति"), _("अभी जारी नहीं")))
        elif obj.must_change_password:
            rows.append((_("प्रमाण-पत्र स्थिति"), _("अस्थायी पासवर्ड सक्रिय")))
        else:
            rows.append((_("प्रमाण-पत्र स्थिति"), _("पासवर्ड निर्धारित")))
    events = AuditEvent.objects.filter(
        target_type=model._meta.label_lower, target_id=obj.pk
    ).select_related("actor")
    from apps.accounts.access import roles_for

    roles = roles_for(request.user)
    final_selection = None
    pending_registrar_release = False
    final_letter = None
    letter_revisions = None
    if kind == "requests":
        from apps.nominations.models import FinalSelection, LetterRevision

        final_selection = FinalSelection.objects.filter(
            request=obj, state=FinalSelection.State.LOCKED
        ).first()
        if final_selection:
            final_letter = (
                LetterRevision.objects.filter(
                    letter__request=obj,
                    letter__kind="final",
                    state=LetterRevision.State.APPROVED,
                    source_selection=final_selection,
                )
                .select_related("letter")
                .first()
            )
        if not roles & {Role.REVIEWER, Role.VC, Role.ADMIN}:
            from apps.nominations.models import FinalRelease
            release = FinalRelease.objects.filter(selection=final_selection).select_related("letter_revision").first() if final_selection else None
            pending_registrar_release = bool(final_selection and not release)
            final_selection = final_selection if release else None
            final_letter = release.letter_revision if release else None
        if bool(roles & {Role.REVIEWER, Role.VC, Role.ADMIN}):
            letter_revisions = (
                LetterRevision.objects.filter(letter__request=obj)
                .select_related("letter", "created_by", "approved_by")
                .order_by("letter__created_at", "-revision")
            )
    can_history = Role.ADMIN in roles
    if not can_history:
        events = events.none()
    event_page = Paginator(events, 20).get_page(request.GET.get("page"))
    event_page.object_list = [present(event) for event in event_page.object_list]
    return render(
        request,
        "office/detail.html",
        {
            "record": obj,
            "kind": kind,
            "title": title,
            "rows": rows,
            "events": event_page,
            "can_history": can_history,
            "can_issue_credentials": kind == "staff"
            and Role.ADMIN in roles
            and obj != request.user,
            "can_write": (write_role in roles or Role.ADMIN in roles)
            and not (kind == "staff" and pk == request.user.pk)
            and not (
                kind == "requests"
                and obj.state not in {RequestDraft.State.DRAFT, RequestDraft.State.RETURNED}
            ),
            "can_submit": kind == "requests"
            and bool(roles & {Role.PROCESSOR, Role.ADMIN})
            and obj.state in {RequestDraft.State.DRAFT, RequestDraft.State.RETURNED},
            "can_return": kind == "requests"
            and bool(roles & {Role.REVIEWER, Role.ADMIN})
            and obj.state == RequestDraft.State.SUBMITTED,
            "can_accept_review": kind == "requests"
            and bool(roles & {Role.REVIEWER, Role.ADMIN})
            and obj.state == RequestDraft.State.SUBMITTED,
            "can_reviewer": kind == "requests"
            and bool(roles & {Role.REVIEWER, Role.VC, Role.ADMIN}),
            "can_generate": kind == "requests"
            and bool(roles & {Role.VC, Role.ADMIN})
            and obj.state == RequestDraft.State.REVIEWED,
            "can_panel_view": kind == "requests"
            and bool(roles & {Role.VC, Role.ADMIN})
            and obj.state == RequestDraft.State.OFFERED,
            "pending_registrar_release": pending_registrar_release,
            "final_selection": final_selection,
            "final_letter": final_letter,
            "letter_revisions": letter_revisions,
            "return_form": RequestReturnForm(initial={"revision": obj.revision})
            if kind == "requests"
            else None,
            "errors": error,
        },
    )
