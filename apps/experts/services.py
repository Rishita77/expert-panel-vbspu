from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.access import require_role
from apps.accounts.models import Role
from apps.accounts.services import current_actor, lock_access
from apps.audit.services import record
from apps.cases.services import EditConflict

from .models import Appointment, Expert


def facts(obj):
    """Audit only reviewed domain fields; never credentials or implicit form data."""
    data = {}
    for field in obj._meta.fields:
        if field.name in {"id", "created_by", "updated_by", "created_at", "updated_at"}:
            continue
        value = getattr(obj, field.name)
        if value is not None and not isinstance(value, (int, bool, str)):
            value = str(value)
        data[field.name] = value
    if isinstance(obj, Expert) and not obj._state.adding:
        data["subjects"] = list(obj.subjects.order_by("name").values_list("name", flat=True))
    return data


def begin(actor):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.MASTER)
    return actor


def check_revision(obj, revision, reason):
    if obj.revision != revision:
        raise EditConflict("रिकॉर्ड बदल चुका है। अपना पाठ सुरक्षित रखें और वर्तमान विवरण की तुलना करें।")
    if not reason.strip():
        raise ValidationError("परिवर्तन का कारण आवश्यक है।")


def persist(actor, obj, before, reason, action="updated"):
    obj.updated_by = actor
    if obj._state.adding:
        obj.created_by = actor
        action = "created"
    else:
        obj.revision += 1
    obj.full_clean(exclude=["sequence"] if isinstance(obj, Expert) else None)
    obj.save()
    record(actor, f"{obj._meta.model_name}.{action}", obj, before, facts(obj), reason)
    return obj


@transaction.atomic
def save_expert(actor, data, revision=0, pk=None):
    actor = begin(actor)
    obj = Expert.objects.select_for_update().get(pk=pk) if pk else Expert()
    before = facts(obj) if pk else {}
    reason = data.get("reason", "")
    if pk:
        check_revision(obj, revision, reason)
    for key in ["name", "category", "mobile", "email", "is_active"]:
        if key in data:
            setattr(obj, key, data[key])
    if "sequence" in data:
        raise ValidationError("स्थायी क्रमांक बदला नहीं जा सकता।")
    if pk and obj.is_active:
        from apps.nominations.models import Assessment

        if Assessment.objects.filter(
            expert=obj, status__in=["retired", "transferred", "deceased", "permanent"]
        ).exists():
            raise ValidationError("स्थायी निष्क्रिय विशेषज्ञ को पुनः सक्रिय नहीं कर सकते।")
    obj.updated_by = actor
    if not pk:
        obj.created_by = actor
    else:
        obj.revision += 1
    obj.full_clean(exclude=["sequence"])
    obj.save()
    if "subjects" in data:
        obj.subjects.set(data["subjects"])
    record(actor, "expert.updated" if pk else "expert.created", obj, before, facts(obj), reason)
    if not pk and data.get("institution") and data.get("academic_designation"):
        save_appointment(
            actor,
            obj.pk,
            {
                "expert_revision": obj.revision,
                "institution": data["institution"],
                "administrative_post": data["administrative_post"],
                "administrative_post_title": data["administrative_post_title"],
                "academic_designation": data["academic_designation"],
                "is_current": True,
                "start_date": None,
                "end_date": None,
                "post_end_date": data["post_end_date"],
                "classification": Appointment.Classification.UNVERIFIED,
                "evidence": "",
            },
        )
    return obj


def validate_intervals(obj):
    if not obj.start_date:
        return
    for other in Appointment.objects.filter(expert=obj.expert).exclude(pk=obj.pk):
        if not other.start_date:
            continue
        # Missing historical end is unknown, whereas a current assignment has an open end.
        if (not other.is_current and not other.end_date) or (
            not obj.is_current and not obj.end_date
        ):
            continue
        if (obj.end_date is None or other.start_date < obj.end_date) and (
            other.end_date is None or obj.start_date < other.end_date
        ):
            raise ValidationError("संस्था कार्यकाल की ज्ञात तिथियाँ दूसरे रिकॉर्ड से टकराती हैं।")


@transaction.atomic
def save_appointment(actor, expert_id, data, revision=0, pk=None):
    actor = begin(actor)
    expert = Expert.objects.select_for_update().get(pk=expert_id)
    if data.get("expert_revision") != expert.revision:
        raise EditConflict("विशेषज्ञ की संस्था या जानकारी बदल गई है। वर्तमान रिकॉर्ड फिर खोलें।")
    obj = (
        Appointment.objects.select_for_update().get(pk=pk, expert=expert)
        if pk
        else Appointment(expert=expert)
    )
    before = facts(obj) if pk else {}
    reason = data.get("reason", "")
    if pk:
        check_revision(obj, revision, reason)
    for key in [
        "institution",
        "administrative_post",
        "administrative_post_title",
        "academic_designation",
        "is_current",
        "start_date",
        "end_date",
        "post_end_date",
        "classification",
        "evidence",
    ]:
        if key in data:
            setattr(obj, key, data[key])
    if not obj.administrative_post:
        obj.administrative_post_title = ""
        obj.post_end_date = None
    elif (
        obj.administrative_post == Appointment.AdministrativePost.OTHER
        and not obj.administrative_post_title.strip()
    ):
        raise ValidationError("अन्य प्रशासनिक पद का नाम आवश्यक है।")
    if obj.classification != "unverified" and not obj.evidence.strip():
        raise ValidationError("रैंक / संस्था वर्गीकरण का सत्यापन सन्दर्भ आवश्यक है।")
    previous = Appointment.objects.filter(expert=expert, is_current=True).exclude(pk=obj.pk).first()
    if obj.is_current and previous:
        if not reason.strip():
            raise ValidationError("वर्तमान संस्था बदलने का कारण आवश्यक है।")
        old = facts(previous)
        previous.is_current = False
        if obj.start_date:
            previous.end_date = obj.start_date
        persist(actor, previous, old, reason, "ended")
    validate_intervals(obj)
    persist(actor, obj, before, reason)
    # Advance the expert revision as well: simultaneous institution editors cannot silently win.
    expert.revision += 1
    expert.updated_by = actor
    expert.save(update_fields=["revision", "updated_by", "updated_at"])
    return obj

