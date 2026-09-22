from django import forms

from apps.experts.models import Expert

from .models import Assessment


class AssessmentForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    expert = forms.ModelChoiceField(Expert.objects.all(), label="विशेषज्ञ")
    status = forms.ChoiceField(choices=Assessment.STATUS, label="उपलब्धता स्थिति")
    conflict = forms.TypedChoiceField(
        choices=[("no", "नहीं"), ("yes", "हाँ")],
        coerce=lambda value: value == "yes",
        label="हित-संघर्ष है?",
    )
    verifier = forms.CharField(max_length=200, label="सत्यापन करने वाले का नाम / पद")
    reason = forms.CharField(
        max_length=1000, widget=forms.Textarea(attrs={"rows": 2}), label="कारण / विवरण"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expert"].widget = forms.HiddenInput()


class GenerateForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)


class FinalSelectionForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    vc_reference = forms.CharField(max_length=500, required=False, label="VC निर्णय सन्दर्भ (वैकल्पिक)")


class ReviewForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=1000,
        required=False,
        label="टिप्पणी / वापसी कारण",
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class PanelChangeStartForm(forms.Form):
    outgoing_expert = forms.ModelChoiceField(
        Expert.objects.none(), required=False, label="बदला जाने वाला विशेषज्ञ"
    )
    reason = forms.CharField(
        max_length=1000, label="कारण", widget=forms.Textarea(attrs={"rows": 2})
    )
    verifier = forms.CharField(max_length=200, label="सत्यापनकर्ता")
    work_not_occurred = forms.BooleanField(required=False, label="चयन कार्य अभी नहीं हुआ है")

    def __init__(self, *args, experts=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["outgoing_expert"].queryset = Expert.objects.filter(pk__in=experts or [])


class PanelChangeSubmitForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    management_reference = forms.CharField(
        max_length=500, required=False, label="संशोधित प्रबन्ध समिति निर्णय सन्दर्भ"
    )
    management_date = forms.DateField(
        required=False, label="संशोधित निर्णय तिथि", widget=forms.DateInput(attrs={"type": "date"})
    )
    vc_reference = forms.CharField(max_length=500, required=False, label="VC प्रतिस्थापन निर्णय सन्दर्भ")
    vc_date = forms.DateField(
        required=False, label="VC निर्णय तिथि", widget=forms.DateInput(attrs={"type": "date"})
    )


class LetterPrepareForm(forms.Form):
    reference = forms.CharField(max_length=500, label="विश्वविद्यालय पत्रांक")
    letter_date = forms.DateField(label="पत्र तिथि", widget=forms.DateInput(attrs={"type": "date"}))


class LetterReviewForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=1000,
        required=False,
        label="टिप्पणी / वापसी कारण",
        widget=forms.Textarea(attrs={"rows": 2}),
    )
