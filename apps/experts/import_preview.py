from django.utils.translation import gettext_lazy
"""All-or-nothing CSV creation for new expert records."""

import csv
import io
from datetime import date
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.access import permitted
from apps.accounts.models import Role
from apps.institutions.models import Institution, Subject

from .models import Appointment, Expert
from .services import save_expert


BULK_EXPERT_SCHEMA = [
    "source_key", "name", "category", "mobile", "email", "institution_name",
    "university_name", "subject_names", "academic_designation",
    "holds_administrative_post", "administrative_post", "administrative_post_title",
    "post_end_date", "is_active",
]


class BulkExpertUploadForm(forms.Form):
    file = forms.FileField(label=gettext_lazy("UTF-8 CSV फ़ाइल (अधिकतम 1 MB, 1,500 पंक्तियाँ)"))


def csv_rows(raw):
    if len(raw) > 1_000_000:
        raise ValidationError(gettext_lazy("फ़ाइल 1 MB से बड़ी है।"))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError(gettext_lazy("UTF-8 CSV निर्यात करें; पुरानी फ़ॉन्ट एन्कोडिंग स्वीकार नहीं है।")) from exc
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if reader.fieldnames != BULK_EXPERT_SCHEMA:
        raise ValidationError(gettext_lazy("स्तम्भ दिए गए प्रारूप से मेल नहीं खाते। सही प्रारूप डाउनलोड करें।"))
    rows = []
    for number, raw_row in enumerate(reader, start=2):
        if number > 1501:
            raise ValidationError(gettext_lazy("अधिकतम 1,500 डेटा पंक्तियाँ स्वीकार हैं।"))
        if None in raw_row or any(value is None for value in raw_row.values()):
            raise ValidationError(f"gettext_lazy(पंक्ति ){number}gettext_lazy(: स्तम्भों की संख्या गलत है।)")
        rows.append((number, {key: value.strip() for key, value in raw_row.items()}))
    if not rows:
        raise ValidationError(gettext_lazy("CSV फ़ाइल में कम-से-कम एक विशेषज्ञ पंक्ति आवश्यक है।"))
    return rows


def exact_name_match(model, value, label, errors, *, university=False):
    matches = model.objects.filter(name__iexact=value, is_active=True)
    if university:
        matches = matches.filter(institution_kind=Institution.Kind.UNIVERSITY)
    count = matches.count()
    if count == 1:
        return matches.first()
    if count == 0:
        errors.append(f"{label}gettext_lazy(: सक्रिय निर्देशिका में स्पष्ट मिलान नहीं मिला।)")
    else:
        errors.append(f"{label}gettext_lazy(: एक से अधिक समान नाम हैं; निर्देशिका पहचान ठीक करें।)")
    return None


def validate_bulk_experts_csv(raw):
    results, source_keys, names = [], set(), set()
    for number, row in csv_rows(raw):
        errors = []

        def required(*keys):
            for key in keys:
                if not row[key]:
                    errors.append(f"{key}gettext_lazy(: आवश्यक है।)")

        required(
            "source_key", "name", "category", "institution_name", "university_name",
            "subject_names", "academic_designation", "holds_administrative_post", "is_active",
        )
        if row["source_key"] in source_keys:
            errors.append(gettext_lazy("source_key इसी फ़ाइल में दोहराया गया है।"))
        source_keys.add(row["source_key"])
        normalized_name = row["name"].casefold()
        if normalized_name in names:
            errors.append(gettext_lazy("name इसी फ़ाइल में दोहराया गया है।"))
        names.add(normalized_name)
        if row["category"] not in Expert.Category.values:
            errors.append(gettext_lazy("category: general, obc, sc या st चुनें।"))
        if row["academic_designation"] not in {
            Appointment.AcademicDesignation.PROFESSOR,
            Appointment.AcademicDesignation.ASSISTANT,
            Appointment.AcademicDesignation.OTHER,
        }:
            errors.append(gettext_lazy("academic_designation: professor, assistant या other चुनें।"))
        if row["holds_administrative_post"] not in {"true", "false"}:
            errors.append(gettext_lazy("holds_administrative_post: true या false लिखें।"))
        if row["is_active"] not in {"true", "false"}:
            errors.append(gettext_lazy("is_active: true या false लिखें।"))
        holds_post = row["holds_administrative_post"] == "true"
        if holds_post:
            allowed_posts = set(Appointment.AdministrativePost.values) - {""}
            if row["administrative_post"] not in allowed_posts:
                errors.append(gettext_lazy("administrative_post: principal, hod या other चुनें।"))
            if row["administrative_post"] == Appointment.AdministrativePost.OTHER and not row["administrative_post_title"]:
                errors.append(gettext_lazy("administrative_post_title: other पद के लिए आवश्यक है।"))
        elif any(row[key] for key in ["administrative_post", "administrative_post_title", "post_end_date"]):
            errors.append(gettext_lazy("प्रशासनिक पद नहीं होने पर उसके सभी स्तम्भ खाली रखें।"))
        try:
            post_end_date = date.fromisoformat(row["post_end_date"]) if row["post_end_date"] else None
        except ValueError:
            post_end_date = None
            errors.append(gettext_lazy("post_end_date: YYYY-MM-DD तिथि अपेक्षित है।"))
        institution = exact_name_match(Institution, row["institution_name"], "institution_name", errors) if row["institution_name"] else None
        university = exact_name_match(Institution, row["university_name"], "university_name", errors, university=True) if row["university_name"] else None
        subjects = []
        subject_names = [value.strip() for value in row["subject_names"].split("|") if value.strip()]
        if len(subject_names) != len(set(value.casefold() for value in subject_names)):
            errors.append(gettext_lazy("subject_names: एक ही विषय दोहराया गया है।"))
        for subject_name in subject_names:
            subject = exact_name_match(Subject, subject_name, "subject_names", errors)
            if subject:
                subjects.append(subject)
        if row["name"] and Expert.objects.filter(name__iexact=row["name"]).exists():
            errors.append(gettext_lazy("name: इसी नाम का विशेषज्ञ पहले से मौजूद है; पहले रिकॉर्ड की जाँच करें।"))
        for key, limit in {"source_key": 100, "name": 200, "mobile": 32, "email": 254}.items():
            if len(row[key]) > limit:
                errors.append(f"{key}gettext_lazy(: पाठ अधिक लम्बा है।)")
        candidate = Expert(name=row["name"], category=row["category"], mobile=row["mobile"], email=row["email"], is_active=row["is_active"] == "true")
        try:
            candidate.clean_fields(exclude=["created_by", "updated_by", "sequence"])
        except ValidationError as exc:
            errors.extend(exc.messages)
        results.append({
            "number": number, "source": row, "errors": errors,
            "data": {
                "institution": institution, "university": university, "subjects": subjects,
                "academic_designation": row["academic_designation"],
                "administrative_post": row["administrative_post"] if holds_post else "",
                "administrative_post_title": row["administrative_post_title"] if holds_post else "",
                "post_end_date": post_end_date if holds_post else None,
            },
        })
    return results


@transaction.atomic
def import_bulk_experts(actor, rows):
    if any(row["errors"] for row in rows):
        raise ValidationError(gettext_lazy("त्रुटिपूर्ण फ़ाइल आयात नहीं की जा सकती।"))
    batch_id = uuid4()
    created = []
    for row in rows:
        data = row["data"]
        created.append(save_expert(actor, {
            "name": row["source"]["name"], "category": row["source"]["category"],
            "mobile": row["source"]["mobile"], "email": row["source"]["email"],
            "subjects": data["subjects"], "is_active": row["source"]["is_active"] == "true",
            "institution": data["institution"], "university": data["university"],
            "academic_designation": data["academic_designation"],
            "administrative_post": data["administrative_post"],
            "administrative_post_title": data["administrative_post_title"],
            "post_end_date": data["post_end_date"],
            "reason": f"Bulk CSV import {batch_id}; source key {row['source']['source_key']}",
        }))
    return created


@permitted(Role.MASTER)
@require_http_methods(["GET", "POST"])
def preview(request):
    form = BulkExpertUploadForm(request.POST or None, request.FILES or None)
    rows = imported = None
    if request.method == "POST" and form.is_valid():
        try:
            rows = validate_bulk_experts_csv(form.cleaned_data["file"].read(1_000_001))
            if request.POST.get("action") == "import" and not any(row["errors"] for row in rows):
                imported = import_bulk_experts(request.user, rows)
        except (ValidationError, csv.Error) as exc:
            form.add_error(None, exc if isinstance(exc, ValidationError) else gettext_lazy("CSV संरचना अमान्य है।"))
    return render(request, "experts/import.html", {"form": form, "rows": rows, "imported": imported})


@permitted(Role.MASTER)
@require_GET
def template(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="vbspu-expert-bulk-template.csv"'
    response.write("\ufeff")
    csv.writer(response).writerow(BULK_EXPERT_SCHEMA)
    return response
