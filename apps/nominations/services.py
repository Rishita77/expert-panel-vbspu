import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import override

from apps.accounts.access import require_role
from apps.accounts.models import Role
from apps.accounts.services import current_actor, lock_access
from apps.audit.services import record
from apps.cases.models import RequestDraft
from apps.cases.services import EditConflict
from apps.experts.models import Expert
from apps.institutions.models import Institution

from .engine import ROLE_LABELS, Candidate, allocate, nomination_year
from .history import verified_history
from .models import (
    AllocationRun,
    Assessment,
    FinalMember,
    FinalSelection,
    Letter,
    LetterEvent,
    LetterRevision,
    PanelChange,
    PanelChangeReviewEvent,
    ReplacementContribution,
    UtilisationEntry,
    UtilisationReversal,
)

PERMANENT = {"retired", "transferred", "deceased", "permanent"}


def actor_for_write(actor):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.PROCESSOR)
    return actor


def actor_for_reviewer(actor):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.REVIEWER, Role.VC)
    return actor


def actor_for_vc(actor):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.VC)
    return actor


def _normalise_reference(reference):
    return " ".join(reference.split()).casefold()


@override("hi")
def _letter_snapshot(kind, source):
    if kind == Letter.Kind.OFFER:
        seats = source.snapshot.get("seats", [])
        return {
            "kind": kind,
            "request": str(source.request),
            "appointment_type": source.request.get_appointment_type_display(),
            "subject": source.request.subject.name if source.request.subject_id else "",
            "selection_date": source.request.selection_date.isoformat()
            if source.request.selection_date
            else "",
            "members": seats,
            "source_revision": source.request_revision,
        }
    if kind == Letter.Kind.FINAL:
        members = [
            {
                "name": member.snapshot["name"],
                "role": member.role,
                "category": member.snapshot.get("category"),
            }
            for member in source.members.filter(selected=True).order_by("role", "position")
        ]
        return {
            "kind": kind,
            "request": str(source.request),
            "appointment_type": source.request.get_appointment_type_display(),
            "subject": source.request.subject.name if source.request.subject_id else "",
            "selection_date": source.request.selection_date.isoformat()
            if source.request.selection_date
            else "",
            "members": members,
            "source_revision": source.revision,
        }
    return {
        "kind": kind,
        "request": str(source.selection.request),
        "change_type": source.change_type,
        "reason": source.reason,
        "outgoing": str(source.outgoing_expert) if source.outgoing_expert_id else "",
        "replacement": str(source.replacement_expert) if source.replacement_expert_id else "",
        "source_revision": source.revision,
    }


@transaction.atomic
def create_letter(actor, kind, source_id, reference, letter_date):
    actor = actor_for_reviewer(actor)
    reference = reference.strip()
    if not reference or not letter_date:
        raise ValidationError("पत्रांक और पत्र तिथि आवश्यक हैं।")
    normalised = _normalise_reference(reference)
    if Letter.objects.filter(normalised_reference=normalised).exists():
        raise ValidationError("यह पत्रांक पहले से दर्ज है।")
    sources = {
        Letter.Kind.OFFER: AllocationRun.objects.select_related("request", "request__subject"),
        Letter.Kind.FINAL: FinalSelection.objects.select_related("request"),
        Letter.Kind.REPLACEMENT: PanelChange.objects.select_related(
            "selection__request", "outgoing_expert", "replacement_expert"
        ),
        Letter.Kind.CANCELLATION: PanelChange.objects.select_related(
            "selection__request", "outgoing_expert", "replacement_expert"
        ),
    }
    source = sources[kind].select_for_update(of=("self",)).get(pk=source_id)
    if kind == Letter.Kind.OFFER:
        if (
            not source.snapshot.get("complete")
            or source.request_revision != source.request.revision
        ):
            raise ValidationError("वर्तमान पूर्ण अनुशंसा से ही प्रस्तावित पैनल पत्र बनाया जा सकता है।")
        request = source.request
    elif kind == Letter.Kind.FINAL:
        if source.state != FinalSelection.State.LOCKED:
            raise ValidationError("केवल लॉक अंतिम चयन का अभिलेख बनाया जा सकता है।")
        request = source.request
    else:
        if source.state != PanelChange.State.CONFIRMED or source.change_type != kind:
            raise ValidationError("केवल पुष्ट परिवर्तन का सूचना पत्र बनाया जा सकता है।")
        request = source.selection.request
    letter = Letter.objects.create(
        request=request,
        kind=kind,
        reference=reference,
        normalised_reference=normalised,
        created_by=actor,
    )
    revision = LetterRevision.objects.create(
        letter=letter,
        revision=1,
        letter_date=letter_date,
        source_run=source if kind == Letter.Kind.OFFER else None,
        source_selection=source if kind == Letter.Kind.FINAL else None,
        source_change=source
        if kind in {Letter.Kind.REPLACEMENT, Letter.Kind.CANCELLATION}
        else None,
        snapshot=_letter_snapshot(kind, source),
        created_by=actor,
    )
    LetterEvent.objects.create(revision=revision, action="prepared", actor=actor)
    record(actor, "letter.prepared", revision, after={"reference": reference, "kind": kind})
    return revision


def _letter_rows(data):
    rows = [
        (
            ROLE_LABELS.get(item.get("role", ""), item.get("role", "")),
            item.get("name", item.get("replacement", "")),
        )
        for item in data.get("members", [])
    ]
    if not rows:
        rows = [
            ("कारण", data.get("reason", "")),
            ("परिवर्तन", f"{data.get('outgoing', '')} → {data.get('replacement', '')}"),
        ]
    return rows


@override("hi")
def render_letter_pdf(revision):
    from django.template.loader import render_to_string

    configured_font = getattr(settings, "LETTER_DEVANAGARI_FONT_PATH", "")
    font_path = Path(configured_font) if configured_font else None
    if font_path and not font_path.is_file():
        raise ValidationError("कॉन्फ़िगर किया गया हिंदी फ़ॉन्ट इस सर्वर पर उपलब्ध नहीं है।")
    logo_path = settings.BASE_DIR / "static" / "letterhead-logo.png"
    document = render_to_string(
        "nominations/letter_pdf.html",
        {
            "revision": revision,
            "data": revision.snapshot,
            "rows": _letter_rows(revision.snapshot),
            "font_url": font_path.as_uri() if font_path else "",
            "logo_url": logo_path.as_uri() if logo_path.is_file() else "",
        },
    )
    configured_browser = getattr(settings, "LETTER_PDF_BROWSER_PATH", "")
    candidates = [
        configured_browser,
        os.environ.get("CHROME_BIN", ""),
        os.environ.get("CHROMIUM_BIN", ""),
        os.environ.get("EDGE_BIN", ""),
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        "msedge",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    browser = next(
        (
            resolved
            for candidate in candidates
            if candidate
            for resolved in [shutil.which(candidate) or candidate]
            if Path(resolved).is_file()
        ),
        None,
    )
    if not browser:
        raise ValidationError("हिंदी PDF बनाने के लिए Chromium, Chrome या Edge सर्वर पर उपलब्ध नहीं है।")
    with tempfile.TemporaryDirectory(prefix="vbspu-letter-") as temporary_directory:
        source = Path(temporary_directory) / "letter.html"
        output = Path(temporary_directory) / "letter.pdf"
        source.write_text(document, encoding="utf-8")
        profile = Path(temporary_directory) / "browser-profile"
        browser_args = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--allow-file-access-from-files",
            "--no-pdf-header-footer",
            f"--user-data-dir={profile}",
            f"--print-to-pdf={output}",
            source.as_uri(),
        ]
        if getattr(settings, "LETTER_PDF_NO_SANDBOX", False):
            browser_args.insert(2, "--no-sandbox")
        completed = subprocess.run(
            browser_args,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode or not output.is_file():
            raise ValidationError("हिंदी PDF रेंडर नहीं हो सका।")
        return output.read_bytes()


@transaction.atomic
def submit_letter(actor, revision_id, revision_number):
    actor = actor_for_reviewer(actor)
    revision = LetterRevision.objects.select_for_update().get(pk=revision_id)
    if (
        revision.state not in {LetterRevision.State.DRAFT, LetterRevision.State.RETURNED}
        or revision.revision != revision_number
    ):
        raise EditConflict("पत्र संशोधन बदल चुका है।")
    revision.state = LetterRevision.State.SUBMITTED
    revision.submitted_at = timezone.now()
    revision.save(update_fields=["state", "submitted_at"])
    LetterEvent.objects.create(revision=revision, action="submitted", actor=actor)
    record(actor, "letter.submitted", revision)
    return revision


@transaction.atomic
def return_letter(actor, revision_id, revision_number, reason):
    actor = actor_for_vc(actor)
    revision = LetterRevision.objects.select_for_update().get(pk=revision_id)
    if revision.state != LetterRevision.State.SUBMITTED or revision.revision != revision_number:
        raise EditConflict("पत्र संशोधन बदल चुका है।")
    if not reason.strip():
        raise ValidationError("वापसी का कारण आवश्यक है।")
    revision.state = LetterRevision.State.RETURNED
    revision.save(update_fields=["state"])
    LetterEvent.objects.create(revision=revision, action="returned", actor=actor, reason=reason)
    record(actor, "letter.returned", revision, reason=reason)
    return revision


@transaction.atomic
def approve_letter(actor, revision_id, revision_number):
    actor = actor_for_vc(actor)
    revision = (
        LetterRevision.objects.select_for_update().select_related("letter").get(pk=revision_id)
    )
    if revision.state == LetterRevision.State.APPROVED:
        return revision
    if revision.state != LetterRevision.State.SUBMITTED or revision.revision != revision_number:
        raise EditConflict("पत्र संशोधन बदल चुका है।")
    pdf = render_letter_pdf(revision)
    checksum = hashlib.sha256(pdf).hexdigest()
    root = Path(settings.PRIVATE_DOCUMENT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    key = f"{revision.letter_id}/{revision.id}.pdf"
    path = root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)
    revision.state = LetterRevision.State.APPROVED
    revision.approved_by = actor
    revision.approved_at = timezone.now()
    revision.pdf_key = key
    revision.checksum = checksum
    revision.save()
    LetterEvent.objects.create(revision=revision, action="approved", actor=actor)
    record(
        actor,
        "letter.approved",
        revision,
        after={"checksum": checksum, "reference": revision.letter.reference},
    )
    return revision


def _selection_issues(selection, require_assessments=True):
    selected = list(selection.members.filter(selected=True).select_related("expert"))
    issues = []
    roles = {role: [m for m in selected if m.role == role] for role in ROLE_LABELS}
    expected = {"vc": 1, "principal": 1, "professor": 4}
    for role, count in expected.items():
        if len(roles[role]) != count:
            issues.append(f"{ROLE_LABELS[role]}: {count} आवश्यक, {len(roles[role])} चुने गए।")
    if len({m.expert_id for m in selected}) != len(selected):
        issues.append("एक ही विशेषज्ञ को दो बार नहीं चुन सकते।")
    # VC remains outside final category coverage, as approved with document 18.
    categories = {m.expert.category for m in selected if m.role != "vc"}
    if not categories & {"sc", "st"}:
        issues.append("SC/ST प्रतिनिधित्व पूरा नहीं है।")
    if "obc" not in categories:
        issues.append("OBC प्रतिनिधित्व पूरा नहीं है।")
    assessment_by_expert = {}
    if require_assessments:
        for assessment in Assessment.objects.filter(
            request=selection.request,
            request_revision=selection.source_run.request_revision,
            allocation_date=selection.source_run.allocation_date,
        ).order_by("-recorded_at"):
            assessment_by_expert.setdefault(assessment.expert_id, assessment)
    for member in selected:
        expert = member.expert
        if not expert.is_active:
            issues.append(f"{expert.name}: विशेषज्ञ निष्क्रिय है।")
        snapshot = member.snapshot
        home = snapshot.get("home") or {}
        if home.get("institution") == str(selection.request.institution_id):
            issues.append(f"{expert.name}: अपने महाविद्यालय के लिए नामांकन वर्जित है।")
        if require_assessments:
            assessment = assessment_by_expert.get(expert.pk)
            if not assessment:
                issues.append(f"{expert.name}: उपलब्धता / हित-संघर्ष सत्यापन शेष है।")
            elif assessment.status != "available" or assessment.conflict:
                issues.append(f"{expert.name}: उपलब्धता या हित-संघर्ष के कारण लॉक नहीं हो सकता।")
    return issues


@transaction.atomic
def create_final_selection(actor, run_id):
    actor = actor_for_vc(actor)
    run = AllocationRun.objects.select_for_update().select_related("request").get(pk=run_id)
    if not run.snapshot.get("complete"):
        raise ValidationError("पूर्ण अनुशंसा से ही अंतिम चयन प्रारूप बनाया जा सकता है।")
    if run.request_revision != run.request.revision:
        raise EditConflict("अनुरोध बदल चुका है। नई अनुशंसा बनाएँ।")
    selection, created = FinalSelection.objects.get_or_create(
        source_run=run,
        defaults={"request": run.request, "created_by": actor, "updated_by": actor},
    )
    if not created:
        return selection
    positions = {role: 0 for role in ROLE_LABELS}
    for seat in run.snapshot["seats"]:
        role = seat["role"]
        positions[role] += 1
        FinalMember.objects.create(
            selection=selection,
            expert_id=seat["id"],
            role=role,
            position=positions[role],
            selected=role in {"vc", "principal", "scst", "obc"},
            snapshot={
                "name": seat["name"],
                "sequence": seat["sequence"],
                "category": seat["category"],
                "allocation_date": run.snapshot["allocation_date"],
                "home": next(
                    (
                        item.get("home")
                        for item in run.snapshot.get("candidate_evidence", [])
                        if item["expert"] == seat["id"]
                    ),
                    None,
                ),
            },
        )
    record(actor, "final_selection.created", selection, after={"run": str(run.pk)})
    return selection


@transaction.atomic
def save_final_selection(actor, selection_id, data, selected_ids):
    actor = actor_for_vc(actor)
    selection = FinalSelection.objects.select_for_update().get(pk=selection_id)
    if selection.state != FinalSelection.State.DRAFT:
        raise ValidationError("इस चयन में अब बदलाव नहीं किया जा सकता।")
    if selection.revision != data["revision"]:
        raise EditConflict("अंतिम चयन बदल चुका है। वर्तमान विवरण फिर खोलें।")
    selected_ids = {str(pk) for pk in selected_ids}
    members = list(selection.members.select_for_update())
    for member in members:
        member.selected = str(member.pk) in selected_ids
        member.save(update_fields=["selected"])
    selection.vc_reference = data["vc_reference"]
    selection.revision += 1
    selection.updated_by = actor
    selection.state = FinalSelection.State.DRAFT
    selection.save()
    record(actor, "final_selection.updated", selection, after={"selected": sorted(selected_ids)})
    return selection


@transaction.atomic
@transaction.atomic
def lock_final_selection(actor, selection_id, revision, reason=""):
    actor = actor_for_vc(actor)
    selection = (
        FinalSelection.objects.select_for_update()
        .select_related("request", "source_run")
        .get(pk=selection_id)
    )
    if selection.state == FinalSelection.State.LOCKED:
        return selection
    if selection.state != FinalSelection.State.DRAFT:
        raise ValidationError("केवल VC के प्रारूप चयन को लॉक किया जा सकता है।")
    if selection.revision != revision:
        raise EditConflict("अंतिम चयन बदल चुका है।")
    issues = _selection_issues(selection, require_assessments=True)
    if issues:
        raise ValidationError(issues)
    now = timezone.now()
    year = nomination_year(timezone.localdate())
    members = list(
        selection.members.select_for_update().filter(selected=True).select_related("expert")
    )
    for member in members:
        UtilisationEntry.objects.create(
            member=member,
            expert=member.expert,
            selection=selection,
            role=member.role,
            appointment_type=selection.request.appointment_type,
            nomination_year=year,
            locked_at=now,
            snapshot={
                "name": member.snapshot["name"],
                "category": member.snapshot["category"],
                "college": str(selection.request.institution_id),
                "subject": str(selection.request.subject_id),
            },
        )
    selection.state = FinalSelection.State.LOCKED
    selection.locked_by = actor
    selection.locked_at = now
    selection.updated_by = actor
    selection.revision += 1
    selection.save()
    record(
        actor,
        "final_selection.locked",
        selection,
        after={"year": year, "members": len(members)},
        reason=reason,
    )
    return selection


def _current_panel_members(selection):
    """Return effective members after confirmed changes, preserving locked sources."""
    members = {
        str(member.expert_id): {
            "expert_id": member.expert_id,
            "role": member.role,
            "member": member,
        }
        for member in selection.members.filter(selected=True)
    }
    for change in selection.changes.filter(state=PanelChange.State.CONFIRMED).order_by(
        "confirmed_at", "id"
    ):
        if change.change_type == PanelChange.Type.CANCELLATION:
            return {}
        members.pop(str(change.outgoing_expert_id), None)
        members[str(change.replacement_expert_id)] = {
            "expert_id": change.replacement_expert_id,
            "role": change.role,
            "member": None,
        }
    return members


def _active_contribution(expert_id, selection):
    entry = (
        UtilisationEntry.objects.filter(
            selection=selection, expert_id=expert_id, reversal__isnull=True
        )
        .select_related("member")
        .first()
    )
    if entry:
        return entry, None
    contribution = (
        ReplacementContribution.objects.filter(
            change__selection=selection, expert_id=expert_id, reversal__isnull=True
        )
        .select_related("change")
        .first()
    )
    return None, contribution


def _recommended_replacement(run, role, excluded):
    role_rows = next(
        (item["rows"] for item in run.snapshot.get("roles", []) if item["key"] == role), []
    )
    for row in role_rows:
        if not row["reasons"] and row["id"] not in excluded:
            return row
    return None


@transaction.atomic
def create_replacement_change(actor, selection_id, outgoing_expert_id, reason, verifier):
    """Generate the new-date rule evidence and reserve its top valid replacement in a draft."""
    actor = actor_for_reviewer(actor)
    selection = (
        FinalSelection.objects.select_for_update().select_related("request").get(pk=selection_id)
    )
    if selection.state != FinalSelection.State.LOCKED:
        raise ValidationError("प्रतिस्थापन केवल लॉक चयन के लिए बनाया जा सकता है।")
    if not reason.strip() or not verifier.strip():
        raise ValidationError("प्रतिस्थापन का कारण और सत्यापनकर्ता आवश्यक हैं।")
    current = _current_panel_members(selection)
    outgoing = current.get(str(outgoing_expert_id))
    if not outgoing:
        raise ValidationError("चुना गया विशेषज्ञ वर्तमान प्रभावी पैनल में नहीं है।")
    # This run uses the replacement's allocation date and the normal SRS engine.
    run = generate(actor, selection.request_id, selection.request.revision, review_generation=False)
    recommended = _recommended_replacement(run, outgoing["role"], set(current))
    if not recommended:
        raise ValidationError("इस भूमिका के लिए अगला योग्य विशेषज्ञ उपलब्ध नहीं है।")
    original_member = outgoing["member"]
    change = PanelChange.objects.create(
        selection=selection,
        change_type=PanelChange.Type.REPLACEMENT,
        outgoing_member=original_member,
        outgoing_expert_id=outgoing["expert_id"],
        replacement_expert_id=recommended["id"],
        role=outgoing["role"],
        source_run=run,
        reason=reason.strip(),
        verifier=verifier.strip(),
        created_by=actor,
        updated_by=actor,
    )
    record(
        actor,
        "panel_change.replacement_drafted",
        change,
        after={
            "outgoing": str(outgoing_expert_id),
            "replacement": recommended["id"],
            "run": str(run.pk),
        },
        reason=reason,
    )
    return change


@transaction.atomic
def create_cancellation_change(actor, selection_id, reason, verifier, work_not_occurred):
    actor = actor_for_reviewer(actor)
    selection = FinalSelection.objects.select_for_update().get(pk=selection_id)
    if selection.state != FinalSelection.State.LOCKED:
        raise ValidationError("रद्दीकरण केवल लॉक चयन के लिए बनाया जा सकता है।")
    if not reason.strip() or not verifier.strip() or not work_not_occurred:
        raise ValidationError("कारण, सत्यापनकर्ता और कार्य न होने की पुष्टि आवश्यक है।")
    if selection.changes.filter(
        state__in=[PanelChange.State.DRAFT, PanelChange.State.SUBMITTED]
    ).exists():
        raise ValidationError("इस चयन के लिए एक परिवर्तन पहले से समीक्षा में है।")
    change = PanelChange.objects.create(
        selection=selection,
        change_type=PanelChange.Type.CANCELLATION,
        reason=reason.strip(),
        verifier=verifier.strip(),
        work_not_occurred=True,
        created_by=actor,
        updated_by=actor,
    )
    record(actor, "panel_change.cancellation_drafted", change, reason=reason)
    return change


def _change_issues(change, require_assessment=False):
    issues = []
    if not change.reason.strip() or not change.verifier.strip():
        issues.append("कारण और सत्यापनकर्ता आवश्यक हैं।")
    if change.change_type == PanelChange.Type.CANCELLATION:
        if not change.work_not_occurred:
            issues.append("चयन कार्य न होने की पुष्टि आवश्यक है।")
        return issues
    if not change.management_reference.strip() or not change.management_date:
        issues.append("प्रबन्ध समिति का संशोधित निर्णय सन्दर्भ और तिथि आवश्यक हैं।")
    if change.role == "vc" and (not change.vc_reference.strip() or not change.vc_date):
        issues.append("VC प्रतिस्थापन निर्णय सन्दर्भ और तिथि आवश्यक हैं।")
    if not change.source_run_id or not change.replacement_expert_id:
        issues.append("नियम-इंजन अनुशंसा आवश्यक है।")
        return issues
    current = _current_panel_members(change.selection)
    if str(change.outgoing_expert_id) not in current:
        issues.append("मूल सदस्य अब प्रभावी पैनल में नहीं है।")
    if str(change.replacement_expert_id) in current:
        issues.append("प्रतिस्थापन व्यक्ति पैनल में पहले से है।")
    proposed = {
        key: value["expert_id"]
        for key, value in current.items()
        if key != str(change.outgoing_expert_id)
    }
    proposed[str(change.replacement_expert_id)] = change.replacement_expert_id
    non_vc_ids = [
        value
        for key, value in proposed.items()
        if current.get(key, {"role": change.role})["role"] != "vc"
    ]
    # The replacement's own role is absent from current after its outgoing person is removed.
    if change.role != "vc":
        non_vc_ids.append(change.replacement_expert_id)
    categories = set(Expert.objects.filter(pk__in=non_vc_ids).values_list("category", flat=True))
    if not categories & {"sc", "st"}:
        issues.append("प्रतिस्थापन के बाद SC/ST प्रतिनिधित्व पूरा नहीं है।")
    if "obc" not in categories:
        issues.append("प्रतिस्थापन के बाद OBC प्रतिनिधित्व पूरा नहीं है।")
    if require_assessment:
        assessment = (
            Assessment.objects.filter(
                request=change.selection.request,
                request_revision=change.source_run.request_revision,
                allocation_date=change.source_run.allocation_date,
                expert_id=change.replacement_expert_id,
            )
            .order_by("-recorded_at")
            .first()
        )
        if not assessment:
            issues.append("प्रतिस्थापन का उपलब्धता / हित-संघर्ष सत्यापन शेष है।")
        elif assessment.status != "available" or assessment.conflict:
            issues.append("प्रतिस्थापन उपलब्ध नहीं है या हित-संघर्ष है।")
    return issues


@transaction.atomic
def submit_panel_change(actor, change_id, revision, data):
    actor = actor_for_reviewer(actor)
    change = PanelChange.objects.select_for_update().get(pk=change_id)
    if change.state not in {PanelChange.State.DRAFT, PanelChange.State.RETURNED}:
        raise ValidationError("केवल प्रारूप / लौटाया गया परिवर्तन प्रस्तुत कर सकते हैं।")
    if change.revision != revision:
        raise EditConflict("परिवर्तन बदल चुका है।")
    for field in ["management_reference", "management_date", "vc_reference", "vc_date"]:
        setattr(change, field, data.get(field, getattr(change, field)))
    issues = _change_issues(change)
    if issues:
        raise ValidationError(issues)
    change.state = PanelChange.State.SUBMITTED
    change.submitted_at = timezone.now()
    change.updated_by = actor
    change.revision += 1
    change.save()
    PanelChangeReviewEvent.objects.create(
        change=change, revision=change.revision, action="submitted", actor=actor
    )
    record(actor, "panel_change.submitted", change)
    return change


@transaction.atomic
def return_panel_change(actor, change_id, revision, reason):
    actor = actor_for_vc(actor)
    change = PanelChange.objects.select_for_update().get(pk=change_id)
    if change.state != PanelChange.State.SUBMITTED or change.revision != revision:
        raise EditConflict("परिवर्तन बदल चुका है।")
    if not reason.strip():
        raise ValidationError("वापसी का कारण आवश्यक है।")
    change.state = PanelChange.State.RETURNED
    change.revision += 1
    change.updated_by = actor
    change.save()
    PanelChangeReviewEvent.objects.create(
        change=change, revision=change.revision, action="returned", actor=actor, reason=reason
    )
    record(actor, "panel_change.returned", change, reason=reason)
    return change


@transaction.atomic
def confirm_panel_change(actor, change_id, revision, reason=""):
    actor = actor_for_vc(actor)
    change = (
        PanelChange.objects.select_for_update(of=("self",))
        .select_related("selection", "replacement_expert")
        .get(pk=change_id)
    )
    if change.state == PanelChange.State.CONFIRMED:
        return change
    if change.state != PanelChange.State.SUBMITTED or change.revision != revision:
        raise EditConflict("परिवर्तन बदल चुका है।")
    issues = _change_issues(
        change, require_assessment=change.change_type == PanelChange.Type.REPLACEMENT
    )
    if issues:
        raise ValidationError(issues)
    now = timezone.now()
    current = _current_panel_members(change.selection)
    if change.change_type == PanelChange.Type.REPLACEMENT:
        original, replacement = _active_contribution(change.outgoing_expert_id, change.selection)
        if not original and not replacement:
            raise ValidationError("मूल सदस्य का सक्रिय उपयोग योगदान नहीं मिला।")
        UtilisationReversal.objects.create(
            entry=original,
            replacement_entry=replacement,
            change=change,
            reason=change.reason,
            reversed_by=actor,
            reversed_at=now,
        )
        ReplacementContribution.objects.create(
            change=change,
            expert=change.replacement_expert,
            role=change.role,
            appointment_type=change.selection.request.appointment_type,
            nomination_year=nomination_year(timezone.localdate()),
            locked_at=now,
            snapshot={
                "college": str(change.selection.request.institution_id),
                "reason": change.reason,
            },
        )
    else:
        for expert_id in current:
            original, replacement = _active_contribution(expert_id, change.selection)
            if original or replacement:
                UtilisationReversal.objects.create(
                    entry=original,
                    replacement_entry=replacement,
                    change=change,
                    reason=change.reason,
                    reversed_by=actor,
                    reversed_at=now,
                )
    change.state = PanelChange.State.CONFIRMED
    change.confirmed_by = actor
    change.confirmed_at = now
    change.updated_by = actor
    change.revision += 1
    change.save()
    PanelChangeReviewEvent.objects.create(
        change=change, revision=change.revision, action="confirmed", actor=actor, reason=reason
    )
    record(
        actor, "panel_change.confirmed", change, after={"type": change.change_type}, reason=reason
    )
    return change


@transaction.atomic
def assess(actor, request_id, expert_id, data, revision, allocation_date=None):
    # Panel availability is recorded by the VC after Registrar scrutiny.
    actor = actor_for_vc(actor)
    case = RequestDraft.objects.select_for_update().get(pk=request_id)
    if case.revision != revision:
        raise EditConflict("अनुरोध बदल चुका है। वर्तमान विवरण फिर खोलें।")
    expert = Expert.objects.select_for_update().get(pk=expert_id)
    obj = Assessment(
        request=case,
        request_revision=revision,
        expert=expert,
        allocation_date=allocation_date or timezone.localdate(),
        recorded_by=actor,
        **{k: data[k] for k in ["status", "conflict", "verifier", "reason"]},
    )
    obj.full_clean()
    obj.save()
    if obj.status in PERMANENT:
        # DEC-037: transfer/retirement is permanent, not just case unavailability.
        before = {"is_active": expert.is_active}
        expert.is_active = False
        expert.revision += 1
        expert.updated_by = actor
        expert.save(update_fields=["is_active", "revision", "updated_by", "updated_at"])
        record(
            actor,
            "expert.permanently_inactive",
            expert,
            before,
            {"is_active": False, "status": obj.status, "verifier": obj.verifier},
            obj.reason,
        )
    record(
        actor,
        "assessment.recorded",
        obj,
        after={
            "expert": str(expert.pk),
            "request": str(case.pk),
            "status": obj.status,
            "conflict": obj.conflict,
            "verifier": obj.verifier,
            "allocation_date": obj.allocation_date.isoformat(),
        },
        reason=obj.reason,
    )
    return obj


def candidate_facts(expert, case, at_date, assessment, permanent, role):
    """Evaluate one expert from the EC-approved expert directory."""
    if role not in ROLE_LABELS:
        raise ValidationError("नामांकन भूमिका आवश्यक है।")
    reasons = []
    if not expert.is_active or str(expert.pk) in permanent:
        reasons.append("विशेषज्ञ निष्क्रिय है (SRS 12/26, DEC-037)।")
    if not expert.category:
        reasons.append("श्रेणी का रिकॉर्ड अपूर्ण है (SRS 6/7)।")
    subject_matches = any(subject.pk == case.subject_id for subject in expert.subjects.all())
    if role == "professor" and not subject_matches:
        reasons.append("अनुरोध विषय विशेषज्ञ के विषयों में दर्ज नहीं है।")
    # Current undated home was explicitly approved for records; known dates still apply.
    homes = [
        h
        for h in expert.appointments.all()
        if (h.start_date is None or h.start_date <= at_date)
        and (h.end_date is None or at_date < h.end_date)
        and (h.is_current or (h.start_date is not None and h.end_date is not None))
    ]
    home = homes[0] if len(homes) == 1 else None
    if not home:
        reasons.append("आवंटन तिथि की संस्था / पद स्पष्ट नहीं है।")
    else:
        if home.institution_id == case.institution_id:
            reasons.append("अपने महाविद्यालय के लिए नामांकन वर्जित है (DEC-024)।")
        if not home.institution.is_active:
            reasons.append("संस्था निष्क्रिय है।")
        if role == "principal":
            if home.administrative_post != "principal":
                reasons.append("प्राचार्य पद आवश्यक है (SRS 5)।")
            elif home.post_end_date and home.post_end_date < at_date:
                reasons.append("प्राचार्य पद आवंटन तिथि से पहले समाप्त हो चुका है।")
        if role in {"professor", "vc"} and home.academic_designation != "professor":
            reasons.append("प्रोफेसर शैक्षणिक पदनाम आवश्यक है (SRS 4/5)।")
        if role in {"scst", "obc"} and (
            home.academic_designation not in {"professor", "assistant"}
        ):
            reasons.append("प्रोफेसर / सहायक प्रोफेसर शैक्षणिक पदनाम आवश्यक है (SRS 6)।")
        if role == "vc":
            if home.institution.is_affiliated_to_vbspu is None:
                reasons.append("VC के लिए VBSPU सम्बद्धता स्पष्ट होना आवश्यक है (SRS 4.1)।")
            elif home.institution.is_affiliated_to_vbspu and (
                home.institution.institution_kind != "college"
                or home.institution.management_type not in {"government", "aided"}
            ):
                reasons.append("VC के लिए बाह्य या सम्बद्ध राजकीय/अनुदानित संस्था आवश्यक है (SRS 4.1)।")
    if role == "scst" and expert.category not in {"sc", "st"}:
        reasons.append("SC/ST श्रेणी आवश्यक है।")
    if role == "obc" and expert.category != "obc":
        reasons.append("OBC श्रेणी आवश्यक है।")
    if assessment:
        if assessment.status != "available":
            reasons.append(f"{assessment.get_status_display()}: {assessment.reason}")
        if assessment.conflict:
            reasons.append(f"इस चयन में हित-संघर्ष: {assessment.reason} (SRS 13)।")
    person = Candidate(
        str(expert.pk),
        expert.name,
        expert.sequence,
        expert.category or "",
        tuple(reasons),
        history=None,
        verified=bool(assessment),
    )
    evidence = {
        "expert": str(expert.pk),
        "revision": expert.revision,
        "name": expert.name,
        "sequence": expert.sequence,
        "category": expert.category,
        "source": "expert_master",
        "role": role,
        "home": {
            "id": str(home.pk),
            "revision": home.revision,
            "institution": str(home.institution_id),
            "institution_name": home.institution.name,
            "administrative_post": home.administrative_post,
            "academic_designation": home.academic_designation,
            "classification": home.classification,
            "subject_matches_request": subject_matches,
        }
        if home
        else None,
        "assessment": {
            "id": str(assessment.pk),
            "verifier": assessment.verifier,
            "recorder": str(assessment.recorded_by_id),
            "reason": assessment.reason,
            "status": assessment.status,
            "conflict": assessment.conflict,
        }
        if assessment
        else None,
        "reasons": reasons,
    }
    return person, evidence


@transaction.atomic
def generate(actor, request_id, revision, review_generation=True):
    actor = actor_for_vc(actor) if review_generation else actor_for_write(actor)
    case = (
        RequestDraft.objects.select_for_update(of=("self",))
        .select_related("institution", "subject")
        .get(pk=request_id)
    )
    if case.revision != revision:
        raise EditConflict("अनुरोध बदल चुका है। वर्तमान विवरण फिर खोलें।")
    if review_generation and case.state not in {
        RequestDraft.State.REVIEWED,
        RequestDraft.State.OFFERED,
    }:
        raise ValidationError("केवल समीक्षक द्वारा स्वीकृत अनुरोध का प्रस्तावित पैनल बनाया जा सकता है।")
    if (
        not case.institution.is_active
        or case.institution.institution_kind != Institution.Kind.COLLEGE
        or not case.subject_id
        or not case.subject.is_active
    ):
        raise ValidationError("सक्रिय महाविद्यालय और विषय का रिकॉर्ड आवश्यक है।")
    at_date = timezone.localdate()
    assessments = {}
    for a in Assessment.objects.filter(
        request=case, request_revision=revision, allocation_date=at_date
    ):
        assessments.setdefault(a.expert_id, a)
    permanent = {
        str(x)
        for x in Assessment.objects.filter(status__in=PERMANENT).values_list("expert_id", flat=True)
    }
    experts = Expert.objects.prefetch_related("subjects", "appointments__institution").order_by(
        "sequence"
    )
    candidates, errors, evidence = {}, {}, []
    sources = [{"title": "EC स्वीकृत विशेषज्ञ निर्देशिका"}]
    for role in ROLE_LABELS:
        candidates[role] = []
        for expert in experts:
            person, facts = candidate_facts(
                expert, case, at_date, assessments.get(expert.pk), permanent, role
            )
            candidates[role].append(person)
            evidence.append(facts)
    history = verified_history({p.id for people in candidates.values() for p in people}, at_date)
    candidates = {
        role: [replace(p, history=history.get(p.id)) for p in people]
        for role, people in candidates.items()
    }
    result = allocate(case.appointment_type, candidates, at_date, errors)
    expert_ids = {seat["id"] for seat in result["seats"]}
    lifetime_counts = {
        str(row["expert_id"]): row["total"]
        for row in UtilisationEntry.objects.filter(expert_id__in=expert_ids, reversal__isnull=True)
        .values("expert_id")
        .annotate(total=Count("id"))
    }
    for seat in result["seats"]:
        seat["lifetime_count"] = lifetime_counts.get(seat["id"], 0)
    result.update(
        {
            "sources": sources,
            "candidate_evidence": evidence,
            "request_name": str(case),
            "request_subject": case.subject.name,
            "request_institution_id": str(case.institution_id),
            "selection_date": case.selection_date.isoformat() if case.selection_date else None,
            "notice": "अनुरोध प्रारूप है। यह जारी पैनल या अंतिम चयन नहीं है।",
        }
    )
    run = AllocationRun.objects.create(
        request=case,
        request_revision=revision,
        created_by=actor,
        allocation_date=at_date,
        snapshot=result,
    )
    record(
        actor,
        "allocation.evaluated",
        run,
        after={"request": str(case.pk), "revision": revision, "complete": result["complete"]},
    )
    if review_generation:
        case.state = RequestDraft.State.OFFERED
        case.updated_by = actor
        case.save(update_fields=["state", "updated_by", "updated_at"])
        record(actor, "request.offered_panel_generated", case, after={"state": case.state})
    return run
