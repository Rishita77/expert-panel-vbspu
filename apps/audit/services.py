from datetime import date, datetime
from uuid import UUID

from .models import AuditEvent


def snapshot(obj, fields):
    result = {}
    for field in fields:
        value = getattr(obj, field)
        if isinstance(value, (date, datetime, UUID)):
            value = str(value)
        result[field] = value
    if "institution_id" in fields:
        result["institution_name"] = str(obj.institution)
    if "subject_id" in fields:
        result["subject_name"] = str(obj.subject) if obj.subject_id else None
    return result


def record(actor, action, obj, before=None, after=None, reason="", system_actor=""):
    return AuditEvent.objects.create(
        actor=actor,
        system_actor=system_actor,
        action=action,
        target_type=obj._meta.label_lower,
        target_id=obj.pk,
        before=before or {},
        after=after or {},
        reason=reason,
    )
