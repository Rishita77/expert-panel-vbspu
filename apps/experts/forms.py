from django import forms
from django.utils.translation import gettext_lazy as _

from apps.cases.forms import RevisionForm
from apps.institutions.models import Institution

from .models import Appointment, Expert


class ExpertForm(RevisionForm):
    institution = forms.ModelChoiceField(
        label=_("वर्तमान संस्था"),
        queryset=Institution.objects.none(),
        required=True,
    )
    university = forms.ModelChoiceField(
        label=_("विश्वविद्यालय"),
        queryset=Institution.objects.none(),
        required=True,
    )
    academic_designation = forms.ChoiceField(
        label=_("शैक्षणिक पदनाम"),
        choices=[
            (Appointment.AcademicDesignation.PROFESSOR, _("प्रोफेसर")),
            (Appointment.AcademicDesignation.ASSOCIATE, _("सह प्राध्यापक")),
            (Appointment.AcademicDesignation.ASSISTANT, _("सहायक प्रोफेसर")),
            (Appointment.AcademicDesignation.OTHER, _("अन्य")),
        ],
        required=True,
    )
    holds_administrative_post = forms.TypedChoiceField(
        choices=[("yes", _("हाँ")), ("no", _("नहीं"))],
        coerce=lambda value: value == "yes",
        label=_("क्या वर्तमान में कोई प्रशासनिक पद धारण करते हैं?"),
        required=True,
        widget=forms.RadioSelect,
    )
    administrative_post = forms.ChoiceField(
        label=_("धारित प्रशासनिक पद"), choices=Appointment.AdministrativePost.choices, required=False
    )
    administrative_post_title = forms.CharField(
        label=_("अन्य प्रशासनिक पद का नाम"), max_length=200, required=False
    )
    post_end_date = forms.DateField(
        label=_("प्रशासनिक पद समाप्ति तिथि"), required=False,
        help_text=_("तिथि ज्ञात न हो तो खाली छोड़ें।"),
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance._state.adding:
            self.fields["institution"].queryset = Institution.objects.filter(is_active=True)
            self.fields["university"].queryset = Institution.objects.filter(
                is_active=True, institution_kind=Institution.Kind.UNIVERSITY
            )
            self.fields.pop("reason")
            self.order_fields(
                [
                    "name",
                    "category",
                    "institution",
                    "university",
                    "academic_designation",
                    "subjects",
                    "holds_administrative_post",
                    "administrative_post",
                    "administrative_post_title",
                    "post_end_date",
                    "mobile",
                    "email",
                    "is_active",
                    "revision",
                ]
            )
        else:
            self.fields.pop("institution")
            self.fields.pop("university")
            self.fields.pop("academic_designation")
            self.fields.pop("holds_administrative_post")
            self.fields.pop("administrative_post")
            self.fields.pop("administrative_post_title")
            self.fields.pop("post_end_date")

    def clean(self):
        cleaned = super().clean()
        if not self.instance._state.adding:
            return cleaned
        if not cleaned.get("holds_administrative_post"):
            cleaned["administrative_post"] = ""
            cleaned["administrative_post_title"] = ""
            cleaned["post_end_date"] = None
        elif not cleaned.get("administrative_post"):
            self.add_error("administrative_post", _("प्रशासनिक पद चुनें।"))
        elif (
            cleaned.get("administrative_post") == Appointment.AdministrativePost.OTHER
            and not cleaned.get("administrative_post_title", "").strip()
        ):
            self.add_error("administrative_post_title", _("प्रशासनिक पद का नाम दर्ज करें।"))
        return cleaned

    class Meta:
        model = Expert
        fields = ["name", "category", "mobile", "email", "subjects", "is_active"]


class AppointmentForm(RevisionForm):
    expert_revision = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    holds_administrative_post = forms.TypedChoiceField(
        choices=[("yes", _("हाँ")), ("no", _("नहीं"))],
        coerce=lambda value: value == "yes",
        label=_("क्या इस अवधि में प्रशासनिक पद धारण किया?"),
        required=True,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["university"].queryset = Institution.objects.filter(
            is_active=True, institution_kind=Institution.Kind.UNIVERSITY
        )
        self.fields["university"].required = True
        self.fields["holds_administrative_post"].initial = (
            "yes" if self.instance.administrative_post else "no"
        )
        self.order_fields([
            "institution", "university", "academic_designation",
            "is_current", "start_date", "end_date",
            "holds_administrative_post", "administrative_post",
            "administrative_post_title", "post_end_date",
            "classification", "evidence", "reason", "revision", "expert_revision",
        ])

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("holds_administrative_post"):
            cleaned["administrative_post"] = ""
            cleaned["administrative_post_title"] = ""
            cleaned["post_end_date"] = None
        elif not cleaned.get("administrative_post"):
            self.add_error("administrative_post", _("प्रशासनिक पद चुनें।"))
        elif (
            cleaned.get("administrative_post") == Appointment.AdministrativePost.OTHER
            and not cleaned.get("administrative_post_title", "").strip()
        ):
            self.add_error("administrative_post_title", _("प्रशासनिक पद का नाम दर्ज करें।"))
        return cleaned

    class Meta:
        model = Appointment
        fields = [
            "institution",
            "university",
            "academic_designation",
            "administrative_post",
            "administrative_post_title",
            "is_current",
            "start_date",
            "end_date",
            "post_end_date",
            "classification",
            "evidence",
        ]
        widgets = {
            name: forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
            for name in ["start_date", "end_date"]
        }


class CheckContextForm(forms.Form):
    at_date = forms.DateField(
        label=_("वैधता जाँच की तिथि"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    college = forms.ModelChoiceField(
        label=_("अनुरोध महाविद्यालय (अपने महाविद्यालय की जाँच)"),
        queryset=Institution.objects.filter(
            institution_kind=Institution.Kind.COLLEGE, is_active=True
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
