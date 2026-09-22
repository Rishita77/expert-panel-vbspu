import secrets

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class StyledAccountForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )


class CredentialIssueForm(StyledAccountForm):
    METHOD_GENERATE = "generate"
    METHOD_SET = "set"
    method = forms.ChoiceField(
        label="अस्थायी पासवर्ड का तरीका",
        choices=[(METHOD_GENERATE, "सुरक्षित पासवर्ड बनाएँ"), (METHOD_SET, "पासवर्ड स्वयं निर्धारित करें")],
        widget=forms.RadioSelect,
        initial=METHOD_GENERATE,
    )
    temporary_password = forms.CharField(
        label="अस्थायी पासवर्ड", required=False, widget=forms.PasswordInput(render_value=False)
    )
    activate = forms.BooleanField(label="पासवर्ड जारी होने पर खाता सक्रिय करें", required=False)
    reason = forms.CharField(label="कारण / प्राधिकरण सन्दर्भ", max_length=500)
    admin_password = forms.CharField(
        label="अपना वर्तमान पासवर्ड", widget=forms.PasswordInput(render_value=False)
    )

    def __init__(self, *args, target=None, **kwargs):
        self.target = target
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("method") == self.METHOD_GENERATE:
            cleaned["temporary_password"] = secrets.token_urlsafe(18)
        elif not cleaned.get("temporary_password"):
            self.add_error("temporary_password", "अस्थायी पासवर्ड आवश्यक है।")
        if cleaned.get("temporary_password") and self.target:
            try:
                validate_password(cleaned["temporary_password"], self.target)
            except ValidationError as exc:
                self.add_error("temporary_password", exc)
        return cleaned


class PasswordChangeForm(StyledAccountForm):
    current_password = forms.CharField(
        label="वर्तमान पासवर्ड", widget=forms.PasswordInput(render_value=False)
    )
    new_password = forms.CharField(
        label="नया पासवर्ड", widget=forms.PasswordInput(render_value=False)
    )
    confirm_password = forms.CharField(
        label="नया पासवर्ड फिर से लिखें", widget=forms.PasswordInput(render_value=False)
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "दोनों नए पासवर्ड समान नहीं हैं।")
        return cleaned


class EmailOtpForm(StyledAccountForm):
    code = forms.CharField(
        label="ईमेल पर भेजा गया छह अंकों का कोड",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code"}),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isascii() or not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("छह अंकों का कोड लिखें।")
        return code
