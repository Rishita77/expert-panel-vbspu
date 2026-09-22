import uuid

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    system_actor = models.CharField(max_length=100, blank=True)
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.UUIDField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [models.Index(fields=["target_type", "target_id", "-occurred_at"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(actor__isnull=False, system_actor="")
                    | (models.Q(actor__isnull=True) & ~models.Q(system_actor=""))
                ),
                name="audit_identified_actor",
            )
        ]
