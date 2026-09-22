import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.expressions import RawSQL


class TrackedRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


class Expert(TrackedRecord):
    class Category(models.TextChoices):
        GENERAL = "general", "सामान्य"
        OBC = "obc", "OBC"
        SC = "sc", "SC"
        ST = "st", "ST"

    name = models.CharField("पूरा नाम", max_length=200)
    sequence = models.BigIntegerField(
        "स्थायी क्रमांक",
        unique=True,
        editable=False,
        db_default=RawSQL("nextval('experts_permanent_sequence')", []),
    )
    category = models.CharField(
        "श्रेणी", max_length=12, choices=Category.choices, null=True, blank=True
    )
    mobile = models.CharField(
        "मोबाइल",
        max_length=32,
        blank=True,
        validators=[RegexValidator(r"^\+?[0-9][0-9 ()-]{4,30}[0-9]$", "मान्य सम्पर्क नम्बर दर्ज करें।")],
    )
    email = models.EmailField("ईमेल", max_length=254, blank=True)
    is_active = models.BooleanField("सक्रिय", default=True)
    subjects = models.ManyToManyField("institutions.Subject", verbose_name="विषय", blank=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(name__regex=r"\S"), name="expert_name_required"
            ),
            models.CheckConstraint(
                condition=models.Q(category__isnull=True)
                | models.Q(category__in=["general", "obc", "sc", "st"]),
                name="expert_category_valid",
            ),
        ]

    def __str__(self):
        return f"{self.name} · #{self.sequence}"


class Appointment(TrackedRecord):
    class AdministrativePost(models.TextChoices):
        NONE = "", "कोई प्रशासनिक पद नहीं"
        PRINCIPAL = "principal", "प्राचार्य"
        HOD = "hod", "विभागाध्यक्ष"
        OTHER = "other", "अन्य प्रशासनिक पद"

    class AcademicDesignation(models.TextChoices):
        PROFESSOR = "professor", "प्रोफेसर"
        ASSISTANT = "assistant", "सहायक प्रोफेसर"
        OTHER = "other", "अन्य"
        UNKNOWN = "unknown", "सत्यापन शेष"

    class Classification(models.TextChoices):
        INTERNAL = "internal", "VBSPU सम्बद्ध आन्तरिक"
        EXTERNAL = "external", "बाह्य"
        UNVERIFIED = "unverified", "सत्यापन शेष"

    expert = models.ForeignKey(Expert, on_delete=models.PROTECT, related_name="appointments")
    institution = models.ForeignKey(
        "institutions.Institution", on_delete=models.PROTECT, verbose_name="संस्था"
    )
    administrative_post = models.CharField(
        "धारित प्रशासनिक पद", max_length=20, choices=AdministrativePost.choices, blank=True
    )
    administrative_post_title = models.CharField(
        "अन्य प्रशासनिक पद का नाम", max_length=200, blank=True
    )
    academic_designation = models.CharField(
        "शैक्षणिक पदनाम",
        max_length=20,
        choices=AcademicDesignation.choices,
        default=AcademicDesignation.UNKNOWN,
    )
    is_current = models.BooleanField("वर्तमान संस्था", default=True)
    start_date = models.DateField("कार्यभार आरम्भ (यदि ज्ञात हो)", null=True, blank=True)
    end_date = models.DateField("कार्यभार समाप्ति — यह तिथि शामिल नहीं है", null=True, blank=True)
    post_end_date = models.DateField("प्रशासनिक पद समाप्ति (यदि ज्ञात हो)", null=True, blank=True)
    classification = models.CharField(
        "आन्तरिक / बाह्य",
        max_length=20,
        choices=Classification.choices,
        default=Classification.UNVERIFIED,
    )
    evidence = models.CharField("पद / रैंक / संस्था सत्यापन सन्दर्भ", max_length=500, blank=True)

    class Meta:
        ordering = ["-is_current", "-start_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["expert"],
                condition=models.Q(is_current=True),
                name="one_current_expert_home",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(start_date__isnull=True)
                | models.Q(end_date__gt=models.F("start_date")),
                name="appointment_dates_ordered",
            ),
            models.CheckConstraint(
                condition=models.Q(is_current=False) | models.Q(end_date__isnull=True),
                name="current_appointment_open_end",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    administrative_post__in=["", "principal", "hod", "other"]
                ),
                name="appointment_administrative_post_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    academic_designation__in=["professor", "assistant", "other", "unknown"]
                ),
                name="appointment_academic_designation_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(classification__in=["internal", "external", "unverified"]),
                name="appointment_classification_valid",
            ),
        ]

    def __str__(self):
        return f"{self.institution} · {self.get_academic_designation_display()}"
