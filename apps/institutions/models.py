import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DirectoryRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("नाम"), max_length=255)
    official_code = models.CharField(_("आधिकारिक कोड (यदि उपलब्ध हो)"), max_length=50, blank=True)
    is_active = models.BooleanField(_("सक्रिय"), default=True)
    revision = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(name__regex=r"\S"), name="%(class)s_name_required"
            )
        ]

    def __str__(self):
        return self.name


class Institution(DirectoryRecord):
    class Kind(models.TextChoices):
        COLLEGE = "college", _("महाविद्यालय")
        UNIVERSITY = "university", _("विश्वविद्यालय")
        OTHER = "other", _("अन्य")

    class Management(models.TextChoices):
        GOVERNMENT = "government", _("सरकारी")
        AIDED = "aided", _("अनुदानित")
        OTHER = "other", _("अन्य")
        UNKNOWN = "unknown", _("अज्ञात")

    district = models.CharField(_("जनपद"), max_length=100, blank=True)
    address = models.TextField(_("पता"), max_length=1000, blank=True)
    institution_kind = models.CharField(_("संस्था का प्रकार"), max_length=20, choices=Kind.choices)
    management_type = models.CharField(
        _("प्रबन्धन प्रकार"), max_length=20, choices=Management.choices, default=Management.UNKNOWN
    )
    is_affiliated_to_vbspu = models.BooleanField(
        _("VBSPU से सम्बद्ध"), null=True, blank=True, default=None
    )

    class Meta(DirectoryRecord.Meta):
        abstract = False
        constraints = [
            *DirectoryRecord.Meta.constraints,
            models.CheckConstraint(
                condition=models.Q(institution_kind__in=["college", "university", "other"]),
                name="known_institution_kind",
            ),
            models.CheckConstraint(
                condition=models.Q(management_type__in=["government", "aided", "other", "unknown"]),
                name="known_management_type",
            ),
        ]


class Subject(DirectoryRecord):
    name = models.CharField(_("विषय का नाम"), max_length=200)
