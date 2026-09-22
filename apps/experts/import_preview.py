"""Bounded, read-only CSV validation. No model/sequence/audit writes."""

import csv
import io
import re
from datetime import date
from uuid import UUID

from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.access import permitted
from apps.accounts.models import Role
from apps.institutions.models import Institution, Subject

from .models import Appointment, Expert

SCHEMAS = {
    "experts": ["source_key", "name", "category", "mobile", "email", "subject_ids"],
    "appointments": [
        "expert_sequence",
        "institution_id",
        "academic_designation",
        "administrative_post",
        "administrative_post_title",
        "classification",
        "evidence",
        "start_date",
        "end_date",
        "post_end_date",
        "is_current",
    ],
}
TITLES = {
    "experts": "विशेषज्ञ",
    "appointments": "संस्था / पद इतिहास",
}


class UploadForm(forms.Form):
    kind = forms.ChoiceField(label="रिकॉर्ड का प्रकार", choices=TITLES.items())
    file = forms.FileField(label="UTF-8 CSV फ़ाइल (अधिकतम 250 KB, 500 पंक्तियाँ)")


def validate_csv(kind, raw):
    if kind not in SCHEMAS:
        raise ValidationError("अमान्य रिकॉर्ड प्रकार।")
    if len(raw) > 250_000:
        raise ValidationError("फ़ाइल 250 KB से बड़ी है।")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("UTF-8 CSV निर्यात करें; पुरानी फ़ॉन्ट एन्कोडिंग स्वीकार नहीं है।") from exc
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if reader.fieldnames != SCHEMAS[kind]:
        raise ValidationError("स्तम्भ दिए गए प्रारूप से मेल नहीं खाते। सही प्रारूप डाउनलोड करें।")
    results, seen = [], set()
    scope_groups = {}
    known_periods = {}
    for number, raw_row in enumerate(reader, start=2):
        if number > 501:
            raise ValidationError("अधिकतम 500 डेटा पंक्तियाँ स्वीकार हैं।")
        if None in raw_row or any(value is None for value in raw_row.values()):
            raise ValidationError(f"पंक्ति {number}: स्तम्भों की संख्या गलत है।")
        row = {key: value.strip() for key, value in raw_row.items()}
        errors, warnings = [], []

        def required(*keys):
            for key in keys:
                if not row[key]:
                    errors.append(f"{key}: आवश्यक है।")

        def choice(key, options, optional=False):
            if not (optional and not row[key]) and row[key] not in options:
                errors.append(f"{key}: मान्य विकल्प {', '.join(options)}।")

        def ref(key, model, optional=False):
            if optional and not row[key]:
                return None
            try:
                if key == "expert_sequence":
                    obj = model.objects.get(sequence=int(row[key]))
                else:
                    obj = model.objects.get(pk=UUID(row[key]))
                return obj
            except (ValueError, model.DoesNotExist):
                errors.append(f"{key}: मौजूदा रिकॉर्ड से स्पष्ट मिलान नहीं मिला।")
                return None

        dates = {}
        for key in SCHEMAS[kind]:
            if key.endswith("_date") or key in {"valid_from", "valid_through"}:
                try:
                    if row[key] and not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row[key]):
                        raise ValueError("Date format")
                    dates[key] = date.fromisoformat(row[key]) if row[key] else None
                except ValueError:
                    errors.append(f"{key}: YYYY-MM-DD तिथि अपेक्षित है।")
        if kind == "experts":
            required("source_key", "name")
            choice("category", Expert.Category.values, optional=True)
            if row["source_key"] in seen:
                errors.append("source_key इसी फ़ाइल में दोहराया गया है।")
            seen.add(row["source_key"])
            expert = Expert(
                name=row["name"],
                category=row["category"] or None,
                mobile=row["mobile"],
                email=row["email"],
            )
            try:
                expert.clean_fields(exclude=["created_by", "updated_by", "sequence"])
            except ValidationError as exc:
                errors.extend(exc.messages)
            if Expert.objects.filter(name__iexact=row["name"]).exists():
                warnings.append("इसी नाम का रिकॉर्ड मौजूद है; व्यक्ति की पहचान की समीक्षा करें।")
            if not row["category"]:
                warnings.append("श्रेणी अज्ञात है; रिकॉर्ड अधूरा रहेगा।")
            for ident in filter(None, row["subject_ids"].split("|")):
                try:
                    Subject.objects.get(pk=UUID(ident))
                except (ValueError, Subject.DoesNotExist):
                    errors.append("subject_ids: विषय का स्पष्ट मिलान नहीं मिला।")
            warnings.append("प्रस्तावित निर्माण क्रम: " + str(number - 1) + "; क्रमांक अभी आरक्षित नहीं है।")
        elif kind == "appointments":
            expert, institution = ref("expert_sequence", Expert), ref("institution_id", Institution)
            choice("academic_designation", Appointment.AcademicDesignation.values)
            choice("administrative_post", Appointment.AdministrativePost.values)
            choice("classification", Appointment.Classification.values)
            choice("is_current", ["true", "false"])
            if (
                row["academic_designation"] in {"professor", "assistant"}
                or row["classification"] != "unverified"
            ):
                required("evidence")
            if row["administrative_post"] == "other":
                required("administrative_post_title")
            if not row["administrative_post"] and (
                row["administrative_post_title"] or row["post_end_date"]
            ):
                errors.append("प्रशासनिक पद न होने पर पद का नाम और समाप्ति तिथि खाली रखें।")
            start, end = dates.get("start_date"), dates.get("end_date")
            if start and end and end <= start:
                errors.append("समाप्ति तिथि आरम्भ तिथि के बाद होनी चाहिए।")
            if row["is_current"] == "true" and row["end_date"]:
                errors.append("वर्तमान संस्था की समाप्ति तिथि खाली रखें।")
            if (
                expert
                and expert.appointments.filter(is_current=True).exists()
                and row["is_current"] == "true"
            ):
                warnings.append("वर्तमान संस्था पहले से है; बदलाव के कारण और इतिहास की समीक्षा आवश्यक है।")
            identity = row["expert_sequence"]
            if start and (end or row["is_current"] == "true"):
                for prior_start, prior_end in known_periods.get(identity, []):
                    if (end is None or prior_start < end) and (
                        prior_end is None or start < prior_end
                    ):
                        errors.append("इसी फ़ाइल में संस्था कार्यकाल की ज्ञात तिथियाँ टकराती हैं।")
                known_periods.setdefault(identity, []).append((start, end))
            if row["is_current"] == "true":
                if identity in seen:
                    errors.append("एक विशेषज्ञ की दो वर्तमान संस्थाएँ इसी फ़ाइल में हैं।")
                seen.add(identity)
            if expert and institution and not errors:
                from .services import validate_intervals

                obj = Appointment(
                    expert=expert,
                    institution=institution,
                    start_date=start,
                    end_date=end,
                    is_current=row["is_current"] == "true",
                )
                try:
                    validate_intervals(obj)
                except ValidationError as exc:
                    errors.extend(exc.messages)
        start = dates.get("effective_date") or dates.get("valid_from")
        if start and dates.get("valid_through") and dates["valid_through"] < start:
            errors.append("वैधता तिथियाँ उलटी हैं।")
        for key, value in row.items():
            limit = {
                "name": 200,
                "authority": 200,
                "reference": 200,
                "title": 200,
                "mobile": 32,
                "email": 254,
                "source_description": 1000,
            }.get(key, 500)
            if len(value) > limit:
                errors.append(f"{key}: पाठ अधिक लम्बा है।")
        results.append({"number": number, "source": row, "errors": errors, "warnings": warnings})
    return results


@permitted(Role.MASTER)
@require_http_methods(["GET", "POST"])
def preview(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    rows = None
    if request.method == "POST" and form.is_valid():
        try:
            rows = validate_csv(form.cleaned_data["kind"], form.cleaned_data["file"].read(250_001))
        except (ValidationError, csv.Error) as exc:
            form.add_error(None, exc if isinstance(exc, ValidationError) else "CSV संरचना अमान्य है।")
    return render(
        request, "experts/import.html", {"form": form, "rows": rows, "schemas": TITLES.items()}
    )


@permitted(Role.MASTER)
@require_GET
def template(request, kind):
    if kind not in SCHEMAS:
        from django.http import Http404

        raise Http404
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="vbspu-{kind}-template.csv"'
    response.write("\ufeff")
    csv.writer(response).writerow(SCHEMAS[kind])
    return response


@permitted(Role.MASTER)
@require_GET
def references(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="vbspu-reference-mapping.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["record_type", "id", "name", "expert_sequence"])
    for name, model in [
        ("institution", Institution),
        ("subject", Subject),
        ("expert", Expert),
    ]:
        for obj in model.objects.all().iterator():
            label = str(obj)
            if label.lstrip().startswith(("=", "+", "-", "@")):
                label = "'" + label
            writer.writerow([name, str(obj.pk), label, obj.sequence if name == "expert" else ""])
    return response
