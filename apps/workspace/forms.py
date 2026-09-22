from django import forms

from apps.nominations.policies import POLICIES


class IntakePreviewForm(forms.Form):
    """SRS field preview, deliberately not a submission or persisted model form.

    All fields are optional: mandatory submission rules await the intake review.
    Bounds protect the preview endpoint and do not establish University policy.
    """

    college_code = forms.CharField(label="महाविद्यालय कोड", max_length=50, required=False)
    college_name = forms.CharField(label="महाविद्यालय का नाम", max_length=255, required=False)
    district = forms.CharField(label="जनपद", max_length=100, required=False)
    college_type = forms.ChoiceField(
        label="महाविद्यालय का प्रकार",
        required=False,
        choices=[
            ("", "चुनें"),
            ("government", "राजकीय"),
            ("aided", "अनुदानित"),
            ("other", "अन्य"),
        ],
    )
    contact_details = forms.CharField(
        label="प्राचार्य / प्रबन्धक का विवरण",
        max_length=500,
        required=False,
    )
    appointment_type = forms.ChoiceField(
        label="नियुक्ति का पद",
        required=False,
        choices=[
            ("", "पद चुनें"),
            *((key, policy.label_hi) for key, policy in POLICIES.items()),
        ],
    )
    subject = forms.CharField(label="विभाग / विषय", max_length=200, required=False)
    vacancy = forms.CharField(label="रिक्ति का स्वरूप", max_length=300, required=False)
    sanctioned_post = forms.CharField(label="स्वीकृत पद का विवरण", max_length=500, required=False)
    advertisement = forms.CharField(label="विज्ञापन सन्दर्भ", max_length=300, required=False)
    selection_date = forms.DateField(
        label="प्रस्तावित चयन तिथि",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    candidate_count = forms.IntegerField(
        label="अभ्यर्थियों की संख्या (यदि उपलब्ध हो)",
        required=False,
        min_value=0,
        max_value=2_147_483_647,
    )
    remarks = forms.CharField(
        label="टिप्पणी",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )
            if isinstance(field, forms.CharField) and not isinstance(field, forms.ChoiceField):
                field.widget.attrs.update({"spellcheck": "false", "lang": "hi"})
            if field.help_text:
                field.widget.attrs["aria-describedby"] = f"id_{name}_helptext"
        self.fields["college_name"].widget.attrs["placeholder"] = "महाविद्यालय का पूरा नाम"
        self.fields["subject"].widget.attrs["placeholder"] = "जैसे: हिन्दी, राजनीति विज्ञान"

    def display_rows(self):
        """Called only after successful validation. Values are escaped by templates."""
        rows = []
        for name, field in self.fields.items():
            value = self.cleaned_data.get(name)
            if isinstance(field, forms.ChoiceField):
                value = dict(field.choices).get(value, "") if value else ""
            elif isinstance(field, forms.DateField) and value:
                value = value.strftime("%d.%m.%Y")
            if value is None or value == "":
                value = "—"
            rows.append((field.label, value))
        return rows
