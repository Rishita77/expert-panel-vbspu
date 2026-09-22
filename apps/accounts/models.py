import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class StaffUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField("पूरा नाम", max_length=200)
    is_active = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    temporary_password_expires_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    session_security_version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("username"), name="staff_username_ci_unique"),
            models.CheckConstraint(
                condition=models.Q(full_name__regex=r"\S"), name="staff_name_required"
            ),
        ]

    def __str__(self):
        return self.full_name or self.username


class Role(models.TextChoices):
    ADMIN = "admin", "सिस्टम प्रशासक"
    MASTER = "master", "निर्देशिका प्रबन्धक"
    PROCESSOR = "processor", "विश्वविद्यालय POC"
    REVIEWER = "reviewer", "रजिस्ट्रार / समीक्षक"
    VC = "vc", "कुलपति"


class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(StaffUser, on_delete=models.PROTECT, related_name="role_assignments")
    role = models.CharField(max_length=20, choices=Role.choices)
    granted_by = models.ForeignKey(StaffUser, on_delete=models.PROTECT, related_name="+", null=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_by = models.ForeignKey(StaffUser, on_delete=models.PROTECT, related_name="+", null=True)
    revoked_at = models.DateTimeField(null=True)
    reason = models.CharField(max_length=500)
    revoked_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(revoked_at__isnull=True),
                name="one_active_role",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=Role.values), name="known_staff_role"
            ),
        ]


class AccessMutex(models.Model):
    """Singleton locked by every account/role mutation, including local setup."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window_started = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)


class EmailLoginChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        StaffUser, on_delete=models.CASCADE, related_name="email_login_challenges"
    )
    otp_hash = models.CharField(max_length=256)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    request_ip_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "sent_at"])]
