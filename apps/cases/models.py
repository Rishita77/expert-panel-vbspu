import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class RequestDraft(models.Model):
    class Appointment(models.TextChoices):
        PRINCIPAL = "principal", _("प्राचार्य")
        HOD = "hod", _("विभागाध्यक्ष")
        SUBJECT = "subject_expert", _("विषय विशेषज्ञ")

    class State(models.TextChoices):
        DRAFT = "draft", _("प्रारूप")
        SUBMITTED = "submitted", _("समीक्षा हेतु प्रस्तुत")
        REVIEWED = "reviewed", _("समीक्षा स्वीकृत · VC कार्रवाई हेतु")
        RETURNED = "returned", _("सुधार हेतु वापस")
        OFFERED = "offered", _("प्रस्तावित पैनल तैयार")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        "institutions.Institution", verbose_name=_("महाविद्यालय"), on_delete=models.PROTECT
    )
    appointment_type = models.CharField(_("नियुक्ति का पद"), max_length=30, choices=Appointment.choices)
    subject = models.ForeignKey(
        "institutions.Subject", verbose_name=_("विषय"), on_delete=models.PROTECT, null=True, blank=True
    )
    contact_details = models.CharField(_("प्राचार्य / प्रबन्धक का विवरण"), max_length=500, blank=True)
    vacancy = models.CharField(_("रिक्ति का स्वरूप"), max_length=300, blank=True)
    sanctioned_post = models.CharField(_("स्वीकृत पद का विवरण"), max_length=500, blank=True)
    advertisement = models.CharField(_("विज्ञापन सन्दर्भ"), max_length=300, blank=True)
    selection_date = models.DateField(_("प्रस्तावित चयन तिथि"), null=True, blank=True)
    candidate_count = models.PositiveIntegerField(_("अभ्यर्थियों की संख्या"), null=True, blank=True)
    remarks = models.TextField(_("टिप्पणी"), max_length=2000, blank=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
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
        ordering = ["-updated_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(appointment_type__in=["principal", "hod", "subject_expert"]),
                name="known_appointment_type",
            )
        ]

    def __str__(self):
        return f"{self.institution} · {self.get_appointment_type_display()}"
