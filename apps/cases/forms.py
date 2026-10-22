from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role, StaffUser
from apps.institutions.models import Institution, Subject

from .models import RequestDraft


class StyledForm:
    def style(self):
        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs["class"] = (
                    "form-check-input"
                    if isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect))
                    else "form-select"
                    if isinstance(field.widget, forms.Select)
                    else "form-control"
                )


class RevisionForm(StyledForm, forms.ModelForm):
    revision = forms.IntegerField(widget=forms.HiddenInput, initial=0, min_value=0)
    reason = forms.CharField(label=_("परिवर्तन का कारण"), max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:
            self.fields["revision"].initial = self.instance.revision
            self.fields["reason"].required = True
        self.style()


class InstitutionForm(RevisionForm):
    is_affiliated_to_vbspu = forms.TypedChoiceField(
        choices=[("yes", _("हाँ")), ("no", _("नहीं"))],
        coerce=lambda value: value == "yes",
        label=_("VBSPU से सम्बद्ध है?"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.fields.pop("reason")
            self.fields["is_affiliated_to_vbspu"].required = True
        else:
            self.fields["is_affiliated_to_vbspu"].initial = (
                "yes" if self.instance.is_affiliated_to_vbspu else "no"
            )

    class Meta:
        model = Institution
        fields = [
            "name",
            "official_code",
            "district",
            "address",
            "institution_kind",
            "management_type",
            "is_affiliated_to_vbspu",
            "is_active",
        ]


class SubjectForm(RevisionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.fields.pop("reason")

    class Meta:
        model = Subject
        fields = ["name", "official_code", "is_active"]


class DraftForm(RevisionForm):
    class Meta:
        model = RequestDraft
        fields = [
            "institution",
            "appointment_type",
            "subject",
            "contact_details",
            "vacancy",
            "sanctioned_post",
            "advertisement",
            "selection_date",
            "candidate_count",
            "remarks",
        ]
        widgets = {
            "selection_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "remarks": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.fields["institution"].queryset = Institution.objects.filter(
            Q(is_active=True, institution_kind=Institution.Kind.COLLEGE)
            | Q(pk=self.instance.institution_id)
        )
        self.fields["subject"].queryset = Subject.objects.filter(
            Q(is_active=True) | Q(pk=self.instance.subject_id)
        )


class RequestReturnForm(StyledForm, forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    reason = forms.CharField(
        label=_("वापसी का कारण"), max_length=500, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.style()


class StaffForm(StyledForm, forms.ModelForm):
    roles = forms.MultipleChoiceField(label=_("अनुमतियाँ"), choices=Role.choices, required=False)
    reason = forms.CharField(label=_("कारण / प्राधिकरण सन्दर्भ"), max_length=500)
    admin_password = forms.CharField(
        label=_("ईमेल बदलने के लिए अपना वर्तमान पासवर्ड"),
        required=False,
        help_text=_("ईमेल में बदलाव न हो तो इसे खाली रखें।"),
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = StaffUser
        fields = ["username", "full_name", "email", "is_active"]
        labels = {"username": _("लॉगिन नाम"), "email": _("आधिकारिक ईमेल"), "is_active": _("सक्रिय खाता")}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.fields.pop("reason")
            self.fields.pop("is_active")
            self.fields.pop("admin_password")
        else:
            self.fields["roles"].initial = list(
                self.instance.role_assignments.filter(revoked_at__isnull=True).values_list(
                    "role", flat=True
                )
            )
        self.style()

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip()
        if cleaned.get("is_active") and not email:
            self.add_error("email", _("सक्रिय खाते के लिए आधिकारिक ईमेल आवश्यक है।"))
        if (
            not self.instance._state.adding
            and email != (self.instance.email or "").strip()
            and not cleaned.get("admin_password")
        ):
            self.add_error("admin_password", _("ईमेल बदलने के लिए अपना वर्तमान पासवर्ड आवश्यक है।"))
        return cleaned
