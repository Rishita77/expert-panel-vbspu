from datetime import timedelta

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record, snapshot

from .access import require_role
from .models import AccessMutex, Role, RoleAssignment, StaffUser

USER_FIELDS = ["username", "full_name", "email", "is_active"]
CREDENTIAL_FIELDS = [
    "is_active",
    "must_change_password",
    "temporary_password_expires_at",
    "password_changed_at",
]


def lock_access():
    # Created in the initial data migration; lock before checking authorisation.
    AccessMutex.objects.select_for_update().get(pk=1)


def current_actor(actor):
    return StaffUser.objects.get(pk=actor.pk)


@transaction.atomic
def save_staff(actor, values, selected_roles, reason, target_id=None):
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.ADMIN)
    if not reason.strip():
        raise ValidationError("परिवर्तन का कारण आवश्यक है।")
    if not set(selected_roles).issubset(Role.values):
        raise ValidationError("अमान्य भूमिका।")
    if target_id == actor.pk:
        raise PermissionDenied("अपने खाते या अनुमतियों को यहाँ नहीं बदल सकते।")
    target = StaffUser.objects.select_for_update().get(pk=target_id) if target_id else StaffUser()
    old = snapshot(target, USER_FIELDS) if target_id else {}
    old_roles = (
        set(target.role_assignments.filter(revoked_at__isnull=True).values_list("role", flat=True))
        if target_id
        else set()
    )
    for field in ["username", "full_name", "email"]:
        setattr(target, field, values[field].strip())
    if target_id and old.get("email", "") != target.email and not actor.check_password(
        values.get("admin_password", "")
    ):
        raise ValidationError("प्रशासक का वर्तमान पासवर्ड सही नहीं है।")
    if target_id:
        target.is_active = values["is_active"]
        if target.is_active and not target.has_usable_password():
            raise ValidationError("पहले खाता प्रमाण-पत्र जारी करें, फिर खाते को सक्रिय करें।")
    else:
        target.is_active = False
        target.set_unusable_password()
    if (
        target_id
        and Role.ADMIN in old_roles
        and (not target.is_active or Role.ADMIN not in selected_roles)
    ):
        other = RoleAssignment.objects.filter(
            role=Role.ADMIN, revoked_at__isnull=True, user__is_active=True
        ).exclude(user=target)
        if not other.exists():
            raise ValidationError("अन्तिम सक्रिय खाता प्रशासक को नहीं हटा सकते।")
    target.full_clean()
    if target_id and old.get("email", "") != target.email:
        target.session_security_version += 1
    target.save()
    now = timezone.now()
    for assignment in target.role_assignments.filter(revoked_at__isnull=True):
        if assignment.role not in selected_roles:
            assignment.revoked_at, assignment.revoked_by = now, actor
            assignment.revoked_reason = reason
            assignment.save(update_fields=["revoked_at", "revoked_by", "revoked_reason"])
    for role in set(selected_roles) - old_roles:
        RoleAssignment.objects.create(user=target, role=role, granted_by=actor, reason=reason)
    record(
        actor,
        "staff.updated" if target_id else "staff.created",
        target,
        {**old, "roles": sorted(old_roles)},
        {**snapshot(target, USER_FIELDS), "roles": sorted(selected_roles)},
        reason,
    )
    return target


@transaction.atomic
def issue_temporary_password(actor, target_id, password, reason, activate=False):
    """Issue a one-time credential without persisting its plaintext anywhere."""
    lock_access()
    actor = current_actor(actor)
    require_role(actor, Role.ADMIN)
    if not reason.strip():
        raise ValidationError("प्रमाण-पत्र जारी करने का कारण आवश्यक है।")
    if not actor.check_password(password["admin_password"]):
        raise ValidationError("प्रशासक का वर्तमान पासवर्ड सही नहीं है।")
    target = StaffUser.objects.select_for_update().get(pk=target_id)
    if target == actor:
        raise PermissionDenied("अपने खाते का पासवर्ड यहाँ से रीसेट नहीं कर सकते।")
    before = snapshot(target, CREDENTIAL_FIELDS)
    validate_password(password["temporary_password"], target)
    target.set_password(password["temporary_password"])
    target.must_change_password = True
    target.temporary_password_expires_at = timezone.now() + timedelta(hours=48)
    target.password_changed_at = timezone.now()
    target.session_security_version += 1
    if activate:
        target.is_active = True
    target.save(
        update_fields=[
            "password",
            "must_change_password",
            "temporary_password_expires_at",
            "password_changed_at",
            "session_security_version",
            "is_active",
            "updated_at",
        ]
    )
    record(
        actor,
        "staff.credentials_issued",
        target,
        before,
        snapshot(target, CREDENTIAL_FIELDS),
        reason,
    )
    return target


@transaction.atomic
def change_own_password(user, current_password, new_password, request=None):
    user = StaffUser.objects.select_for_update().get(pk=user.pk)
    if not user.check_password(current_password):
        raise ValidationError("वर्तमान पासवर्ड सही नहीं है।")
    validate_password(new_password, user)
    before = snapshot(user, CREDENTIAL_FIELDS)
    user.set_password(new_password)
    user.must_change_password = False
    user.temporary_password_expires_at = None
    user.password_changed_at = timezone.now()
    user.session_security_version += 1
    user.save(
        update_fields=[
            "password",
            "must_change_password",
            "temporary_password_expires_at",
            "password_changed_at",
            "session_security_version",
            "updated_at",
        ]
    )
    record(user, "staff.password_changed", user, before, snapshot(user, CREDENTIAL_FIELDS))
    if request is not None:
        update_session_auth_hash(request, user)
    return user
