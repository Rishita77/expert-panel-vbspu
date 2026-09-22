import uuid

from django.conf import settings
from django.db import models


class Assessment(models.Model):
    """Append-only staff declaration; DEC-037 does not require document upload."""

    STATUS = [
        ("available", "उपलब्ध"),
        ("unavailable", "उपलब्ध नहीं"),
        ("leave", "अवकाश पर"),
        ("retired", "सेवानिवृत्त — स्थायी निष्क्रिय"),
        ("transferred", "स्थानान्तरित — स्थायी निष्क्रिय"),
        ("deceased", "दिवंगत"),
        ("temporary", "इस चयन के लिए अयोग्य"),
        ("permanent", "स्थायी निष्क्रिय"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey("cases.RequestDraft", on_delete=models.PROTECT)
    request_revision = models.PositiveIntegerField()
    expert = models.ForeignKey("experts.Expert", on_delete=models.PROTECT)
    allocation_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS)
    conflict = models.BooleanField()
    verifier = models.CharField(max_length=200)
    reason = models.CharField(max_length=1000)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(verifier__regex=r"\S"), name="assessment_verifier_required"
            ),
            models.CheckConstraint(
                condition=models.Q(reason__regex=r"\S"), name="assessment_reason_required"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "available",
                        "unavailable",
                        "leave",
                        "retired",
                        "transferred",
                        "deceased",
                        "temporary",
                        "permanent",
                    ]
                ),
                name="assessment_status_valid",
            ),
        ]


class AllocationRun(models.Model):
    """Immutable evaluated facts; not an offer, approval or final selection."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey("cases.RequestDraft", on_delete=models.PROTECT)
    request_revision = models.PositiveIntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    allocation_date = models.DateField()
    snapshot = models.JSONField()

    class Meta:
        ordering = ["-created_at", "id"]


class FinalSelection(models.Model):
    """VC's final choices from one immutable complete offered panel."""

    class State(models.TextChoices):
        DRAFT = "draft", "प्रारूप"
        LOCKED = "locked", "अंतिम रूप से लॉक"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey("cases.RequestDraft", on_delete=models.PROTECT)
    source_run = models.OneToOneField(AllocationRun, on_delete=models.PROTECT)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    revision = models.PositiveIntegerField(default=1)
    vc_reference = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(state__in=["draft", "locked"]),
                name="final_selection_state_valid",
            )
        ]


class FinalMember(models.Model):
    """Snapshot of an offered component and the VC's final choice."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    selection = models.ForeignKey(FinalSelection, on_delete=models.PROTECT, related_name="members")
    expert = models.ForeignKey("experts.Expert", on_delete=models.PROTECT)
    role = models.CharField(
        max_length=20,
        choices=[
            ("vc", "कुलपति नामित"),
            ("principal", "प्राचार्य"),
            ("professor", "प्रोफेसर"),
            ("scst", "अतिरिक्त SC/ST"),
            ("obc", "अतिरिक्त OBC"),
        ],
    )
    position = models.PositiveSmallIntegerField(default=1)
    selected = models.BooleanField(default=False)
    snapshot = models.JSONField()

    class Meta:
        ordering = ["role", "position", "expert__sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["selection", "expert"], name="final_member_unique_person"
            ),
            models.UniqueConstraint(
                fields=["selection", "role", "position"], name="final_member_unique_seat"
            ),
        ]


class UtilisationEntry(models.Model):
    """One immutable +1 contribution created only within a final lock transaction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.OneToOneField(FinalMember, on_delete=models.PROTECT, related_name="utilisation")
    expert = models.ForeignKey("experts.Expert", on_delete=models.PROTECT)
    selection = models.ForeignKey(FinalSelection, on_delete=models.PROTECT)
    role = models.CharField(max_length=20)
    appointment_type = models.CharField(max_length=30)
    nomination_year = models.CharField(max_length=9)
    locked_at = models.DateTimeField()
    snapshot = models.JSONField()


class PanelChange(models.Model):
    """A separate, reviewed change to an immutable locked final selection."""

    class Type(models.TextChoices):
        REPLACEMENT = "replacement", "प्रतिस्थापन"
        CANCELLATION = "cancellation", "रद्दीकरण"

    class State(models.TextChoices):
        DRAFT = "draft", "प्रारूप"
        SUBMITTED = "submitted", "समीक्षा हेतु प्रस्तुत"
        RETURNED = "returned", "वापस किया गया"
        CONFIRMED = "confirmed", "पुष्ट"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    selection = models.ForeignKey(FinalSelection, on_delete=models.PROTECT, related_name="changes")
    change_type = models.CharField(max_length=20, choices=Type.choices)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    revision = models.PositiveIntegerField(default=1)
    outgoing_member = models.ForeignKey(
        FinalMember,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outgoing_changes",
    )
    outgoing_expert = models.ForeignKey(
        "experts.Expert",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outgoing_panel_changes",
    )
    replacement_expert = models.ForeignKey(
        "experts.Expert",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replacement_changes",
    )
    role = models.CharField(max_length=20, blank=True)
    source_run = models.ForeignKey(AllocationRun, on_delete=models.PROTECT, null=True, blank=True)
    reason = models.CharField(max_length=1000)
    verifier = models.CharField(max_length=200)
    work_not_occurred = models.BooleanField(default=False)
    management_reference = models.CharField(max_length=500, blank=True)
    management_date = models.DateField(null=True, blank=True)
    vc_reference = models.CharField(max_length=500, blank=True)
    vc_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(change_type__in=["replacement", "cancellation"]),
                name="panel_change_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["draft", "submitted", "returned", "confirmed"]),
                name="panel_change_state_valid",
            ),
        ]


class PanelChangeReviewEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change = models.ForeignKey(PanelChange, on_delete=models.PROTECT, related_name="review_events")
    revision = models.PositiveIntegerField()
    action = models.CharField(
        max_length=20, choices=[("submitted", "प्रस्तुत"), ("returned", "वापस"), ("confirmed", "पुष्ट")]
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=1000, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)


class UtilisationReversal(models.Model):
    """One immutable reversal for one original locked contribution."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.OneToOneField(
        UtilisationEntry, on_delete=models.PROTECT, related_name="reversal", null=True, blank=True
    )
    replacement_entry = models.OneToOneField(
        "ReplacementContribution",
        on_delete=models.PROTECT,
        related_name="reversal",
        null=True,
        blank=True,
    )
    change = models.ForeignKey(PanelChange, on_delete=models.PROTECT, related_name="reversals")
    reason = models.CharField(max_length=1000)
    reversed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reversed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(entry__isnull=False, replacement_entry__isnull=True)
                    | models.Q(entry__isnull=True, replacement_entry__isnull=False)
                ),
                name="reversal_has_one_contribution",
            )
        ]


class ReplacementContribution(models.Model):
    """The +1 contribution for a confirmed replacement, linked to its change."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change = models.OneToOneField(
        PanelChange, on_delete=models.PROTECT, related_name="contribution"
    )
    expert = models.ForeignKey("experts.Expert", on_delete=models.PROTECT)
    role = models.CharField(max_length=20)
    appointment_type = models.CharField(max_length=30)
    nomination_year = models.CharField(max_length=9)
    locked_at = models.DateTimeField()
    snapshot = models.JSONField()


class Letter(models.Model):
    """A staff-referenced document with immutable reviewer-approved revisions."""

    class Kind(models.TextChoices):
        OFFER = "offer", "प्रस्तावित पैनल"
        FINAL = "final", "अंतिम चयन अभिलेख"
        REPLACEMENT = "replacement", "प्रतिस्थापन सूचना"
        CANCELLATION = "cancellation", "रद्दीकरण सूचना"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        "cases.RequestDraft", on_delete=models.PROTECT, related_name="letters"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    reference = models.CharField(max_length=500)
    normalised_reference = models.CharField(max_length=500, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]


class LetterRevision(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft", "प्रारूप"
        SUBMITTED = "submitted", "समीक्षा हेतु प्रस्तुत"
        RETURNED = "returned", "वापस किया गया"
        APPROVED = "approved", "डाउनलोड हेतु स्वीकृत"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter = models.ForeignKey(Letter, on_delete=models.PROTECT, related_name="revisions")
    revision = models.PositiveIntegerField()
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    letter_date = models.DateField()
    source_run = models.ForeignKey(AllocationRun, on_delete=models.PROTECT, null=True, blank=True)
    source_selection = models.ForeignKey(
        FinalSelection, on_delete=models.PROTECT, null=True, blank=True
    )
    source_change = models.ForeignKey(PanelChange, on_delete=models.PROTECT, null=True, blank=True)
    snapshot = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    pdf_key = models.CharField(max_length=500, blank=True)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-revision"]
        constraints = [
            models.UniqueConstraint(fields=["letter", "revision"], name="letter_revision_unique"),
            models.CheckConstraint(
                condition=models.Q(state__in=["draft", "submitted", "returned", "approved"]),
                name="letter_revision_state_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        source_run__isnull=False,
                        source_selection__isnull=True,
                        source_change__isnull=True,
                    )
                    | models.Q(
                        source_run__isnull=True,
                        source_selection__isnull=False,
                        source_change__isnull=True,
                    )
                    | models.Q(
                        source_run__isnull=True,
                        source_selection__isnull=True,
                        source_change__isnull=False,
                    )
                ),
                name="letter_revision_one_source",
            ),
        ]


class LetterEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision = models.ForeignKey(LetterRevision, on_delete=models.PROTECT, related_name="events")
    action = models.CharField(
        max_length=20,
        choices=[
            ("prepared", "तैयार"),
            ("submitted", "प्रस्तुत"),
            ("returned", "वापस"),
            ("approved", "स्वीकृत"),
            ("downloaded", "डाउनलोड"),
        ],
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=1000, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
