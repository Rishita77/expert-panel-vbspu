"""All-or-nothing CSV creation for institution directory records."""

import csv
import io
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.access import permitted
from apps.accounts.models import Role
from apps.cases.services import save_record

from .models import Institution


INSTITUTION_SCHEMA = [
    "source_key",
    "name",
    "official_code",
    "district",
    "address",
    "institution_kind",
    "management_type",
    "is_affiliated_to_vbspu",
    "is_active",
]


class InstitutionUploadForm(forms.Form):
    file = forms.FileField(label="UTF-8 CSV फ़ाइल (अधिकतम 250 KB, 500 पंक्तियाँ)")


def csv_rows(raw):
    if len(raw) > 250_000:
        raise ValidationError("फ़ाइल 250 KB से बड़ी है।")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("UTF-8 CSV निर्यात करें; पुरानी फ़ॉन्ट एन्कोडिंग स्वीकार नहीं है।") from exc
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if reader.fieldnames != INSTITUTION_SCHEMA:
        raise ValidationError("स्तम्भ दिए गए प्रारूप से मेल नहीं खाते। सही प्रारूप डाउनलोड करें।")
    rows = []
    for number, raw_row in enumerate(reader, start=2):
        if number > 501:
            raise ValidationError("अधिकतम 500 डेटा पंक्तियाँ स्वीकार हैं।")
        if None in raw_row or any(value is None for value in raw_row.values()):
            raise ValidationError(f"पंक्ति {number}: स्तम्भों की संख्या गलत है।")
        rows.append((number, {key: value.strip() for key, value in raw_row.items()}))
    if not rows:
        raise ValidationError("CSV फ़ाइल में कम-से-कम एक संस्था पंक्ति आवश्यक है।")
    return rows


def validate_institutions_csv(raw):
    results, source_keys, names, codes = [], set(), set(), set()
    for number, row in csv_rows(raw):
        errors = []

        def required(*keys):
            for key in keys:
                if not row[key]:
                    errors.append(f"{key}: आवश्यक है।")

        required(
            "source_key",
            "name",
            "institution_kind",
            "management_type",
            "is_affiliated_to_vbspu",
            "is_active",
        )
        if row["source_key"] in source_keys:
            errors.append("source_key इसी फ़ाइल में दोहराया गया है।")
        source_keys.add(row["source_key"])
        normalized_name = row["name"].casefold()
        if normalized_name in names:
            errors.append("name इसी फ़ाइल में दोहराया गया है।")
        names.add(normalized_name)
        if row["name"] and Institution.objects.filter(name__iexact=row["name"]).exists():
            errors.append("name: इसी नाम की संस्था पहले से मौजूद है।")
        if row["official_code"]:
            normalized_code = row["official_code"].casefold()
            if normalized_code in codes:
                errors.append("official_code इसी फ़ाइल में दोहराया गया है।")
            codes.add(normalized_code)
            if Institution.objects.filter(official_code__iexact=row["official_code"]).exists():
                errors.append("official_code: यह आधिकारिक कोड पहले से मौजूद है।")
        if row["institution_kind"] not in Institution.Kind.values:
            errors.append("institution_kind: college, university या other चुनें।")
        if row["management_type"] not in Institution.Management.values:
            errors.append("management_type: government, aided, other या unknown चुनें।")
        if row["is_affiliated_to_vbspu"] not in {"true", "false"}:
            errors.append("is_affiliated_to_vbspu: true या false लिखें।")
        if row["is_active"] not in {"true", "false"}:
            errors.append("is_active: true या false लिखें।")
        for key, limit in {
            "source_key": 100,
            "name": 255,
            "official_code": 50,
            "district": 100,
            "address": 1000,
        }.items():
            if len(row[key]) > limit:
                errors.append(f"{key}: पाठ अधिक लम्बा है।")
        candidate = Institution(
            name=row["name"],
            official_code=row["official_code"],
            district=row["district"],
            address=row["address"],
            institution_kind=row["institution_kind"],
            management_type=row["management_type"],
            is_affiliated_to_vbspu=row["is_affiliated_to_vbspu"] == "true",
            is_active=row["is_active"] == "true",
        )
        try:
            candidate.clean_fields(exclude=["created_by", "updated_by"])
        except ValidationError as exc:
            errors.extend(exc.messages)
        results.append({"number": number, "source": row, "errors": errors, "data": candidate})
    return results


@transaction.atomic
def import_institutions(actor, rows):
    if any(row["errors"] for row in rows):
        raise ValidationError("त्रुटिपूर्ण फ़ाइल आयात नहीं की जा सकती।")
    batch_id = uuid4()
    created = []
    for row in rows:
        data = row["data"]
        created.append(
            save_record(
                actor,
                Institution,
                {
                    "name": data.name,
                    "official_code": data.official_code,
                    "district": data.district,
                    "address": data.address,
                    "institution_kind": data.institution_kind,
                    "management_type": data.management_type,
                    "is_affiliated_to_vbspu": data.is_affiliated_to_vbspu,
                    "is_active": data.is_active,
                    "reason": f"Bulk CSV import {batch_id}; source key {row['source']['source_key']}",
                },
                revision=0,
            )
        )
    return created


@permitted(Role.MASTER)
@require_http_methods(["GET", "POST"])
def upload(request):
    form = InstitutionUploadForm(request.POST or None, request.FILES or None)
    rows = imported = None
    if request.method == "POST" and form.is_valid():
        try:
            rows = validate_institutions_csv(form.cleaned_data["file"].read(250_001))
            if request.POST.get("action") == "import" and not any(row["errors"] for row in rows):
                imported = import_institutions(request.user, rows)
        except (ValidationError, csv.Error) as exc:
            form.add_error(None, exc if isinstance(exc, ValidationError) else "CSV संरचना अमान्य है।")
    return render(request, "institutions/bulk_import.html", {"form": form, "rows": rows, "imported": imported})


@permitted(Role.MASTER)
@require_GET
def template(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="vbspu-institution-bulk-template.csv"'
    response.write("\ufeff")
    csv.writer(response).writerow(INSTITUTION_SCHEMA)
    return response
