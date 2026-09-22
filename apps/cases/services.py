from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.access import require_role
from apps.accounts.models import Role
from apps.accounts.services import current_actor, lock_access
from apps.audit.services import record, snapshot
from apps.institutions.models import Institution, Subject

from .models import RequestDraft

CASE_FIELDS = [
    "institution_id",
    "appointment_type",
    "subject_id",
    "contact_details",
    "vacancy",
    "sanctioned_post",
    "advertisement",
    "selection_date",
    "candidate_count",
    "remarks",
    "revision",
]
DIRECTORY_FIELDS = ["name", "official_code", "is_active", "revision"]
INSTITUTION_FIELDS = [
    "district",
    "address",
    "institution_kind",
    "management_type",
    "is_affiliated_to_vbspu",
]


class EditConflict(ValidationError):
    pass


@transaction.atomic
def submit_request(actor, request_id, revision):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.PROCESSOR)
    request = RequestDraft.objects.select_for_update().get(pk=request_id)
    if request.revision != revision:
        raise EditConflict("अनुरोध बदल चुका है। वर्तमान विवरण फिर खोलें।")
    if request.state not in {RequestDraft.State.DRAFT, RequestDraft.State.RETURNED}:
        raise ValidationError("केवल प्रारूप या वापस किया गया अनुरोध समीक्षा हेतु प्रस्तुत हो सकता है।")
    request.state = RequestDraft.State.SUBMITTED
    request.updated_by = actor
    request.save(update_fields=["state", "updated_by", "updated_at"])
    record(actor, "request.submitted", request, after={"state": request.state})
    return request


@transaction.atomic
def return_request(actor, request_id, revision, reason):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.REVIEWER)
    request = RequestDraft.objects.select_for_update().get(pk=request_id)
    if request.revision != revision:
        raise EditConflict("अनुरोध बदल चुका है। वर्तमान विवरण फिर खोलें।")
    if request.state != RequestDraft.State.SUBMITTED:
        raise ValidationError("केवल समीक्षा हेतु प्रस्तुत अनुरोध वापस किया जा सकता है।")
    if not reason.strip():
        raise ValidationError("वापसी का कारण आवश्यक है।")
    request.state = RequestDraft.State.RETURNED
    request.updated_by = actor
    request.save(update_fields=["state", "updated_by", "updated_at"])
    record(actor, "request.returned", request, after={"state": request.state}, reason=reason)
    return request


@transaction.atomic
def approve_review(actor, request_id, revision):
    """Record the Registrar's scrutiny decision before the VC sees an allocation action."""
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.REVIEWER)
    request = RequestDraft.objects.select_for_update().get(pk=request_id)
    if request.revision != revision:
        raise EditConflict("अनुरोध बदल चुका है। वर्तमान विवरण फिर खोलें।")
    if request.state != RequestDraft.State.SUBMITTED:
        raise ValidationError("केवल समीक्षा हेतु प्रस्तुत अनुरोध को समीक्षा-स्वीकृति दी जा सकती है।")
    request.state = RequestDraft.State.REVIEWED
    request.updated_by = actor
    request.save(update_fields=["state", "updated_by", "updated_at"])
    record(actor, "request.review_accepted", request, after={"state": request.state})
    return request


@transaction.atomic
def save_record(actor, model, data, revision, target_id=None):
    lock_access()
    actor = current_actor(actor)
    is_case = model is RequestDraft
    require_role(actor, Role.PROCESSOR if is_case else Role.MASTER)
    obj = model.objects.select_for_update().get(pk=target_id) if target_id else model()
    fields = CASE_FIELDS if is_case else DIRECTORY_FIELDS
    if model is Institution:
        fields = fields + INSTITUTION_FIELDS
    before = snapshot(obj, fields) if target_id else {}
    if target_id and revision != obj.revision:
        raise EditConflict(
            "यह रिकॉर्ड किसी अन्य अधिकारी ने बदल दिया है। "
            "आपका पाठ नीचे सुरक्षित है; वर्तमान रिकॉर्ड नए टैब में खोलकर तुलना करें।"
        )
    if (
        is_case
        and target_id
        and obj.state
        not in {
            RequestDraft.State.DRAFT,
            RequestDraft.State.RETURNED,
        }
    ):
        raise ValidationError("समीक्षा में या पैनल तैयार होने के बाद अनुरोध बदला नहीं जा सकता।")
    if is_case:
        college = Institution.objects.get(pk=data["institution"].pk)
        if (not target_id or obj.institution_id != college.pk) and not (
            college.is_active and college.institution_kind == Institution.Kind.COLLEGE
        ):
            raise ValidationError("नए चयन के लिए सक्रिय महाविद्यालय आवश्यक है।")
        subject = data.get("subject")
        if subject and (not target_id or obj.subject_id != subject.pk):
            if not Subject.objects.get(pk=subject.pk).is_active:
                raise ValidationError("नया विषय चयन सक्रिय होना चाहिए।")
    for key, value in data.items():
        if key not in {"revision", "reason"}:
            setattr(obj, key, value.strip() if isinstance(value, str) else value)
    obj.updated_by = actor
    if not target_id:
        obj.created_by = actor
    else:
        obj.revision += 1
    obj.full_clean()
    obj.save()
    record(
        actor,
        f"{model._meta.model_name}.{'updated' if target_id else 'created'}",
        obj,
        before,
        snapshot(obj, fields),
        data.get("reason", ""),
    )
    return obj
