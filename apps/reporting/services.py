"""One read-only reporting path over the immutable nomination ledger."""

from collections import defaultdict
from datetime import date

from django.db.models import Q
from django.utils import timezone

from apps.cases.models import RequestDraft
from apps.experts.models import Appointment, Expert
from apps.institutions.models import Institution, Subject
from apps.nominations.engine import ROLE_LABELS, nomination_year
from apps.nominations.models import (
    FinalSelection,
    Letter,
    LetterRevision,
    PanelChange,
    ReplacementContribution,
    UtilisationEntry,
    UtilisationReversal,
)


REPORTS = {
    "professors": ("REP-01", "प्रोफेसर-वार नामांकन", "role"),
    "principals": ("REP-02", "प्राचार्य-वार नामांकन", "role"),
    "vc-nominees": ("REP-03", "कुलपति नामित उपयोग", "role"),
    "committees": ("REP-04", "महाविद्यालय-वार चयन समितियाँ", "committees"),
    "subjects": ("REP-05", "विषय-वार नामांकन", "subjects"),
    "months": ("REP-06", "माह-वार नामांकन", "months"),
    "annual-utilisation": ("REP-07", "जुलाई-जून वार्षिक उपयोग", "annual"),
    "scst-representation": ("REP-08", "SC/ST प्रतिनिधित्व", "representation_scst"),
    "obc-representation": ("REP-09", "OBC प्रतिनिधित्व", "representation_obc"),
    "not-nominated": ("REP-10", "वर्ष में नामांकित नहीं हुए विशेषज्ञ", "not_nominated"),
    "maximum-nominations": ("REP-11", "सर्वाधिक नामांकित विशेषज्ञ", "maximum"),
    "cancellations": ("REP-12", "रद्द नामांकन", "cancellations"),
    "replacements": ("REP-13", "प्रतिस्थापन विशेषज्ञ", "replacements"),
    "manual-deviations": ("REP-14", "मान्य मैनुअल विचलन", "unavailable_deviations"),
    "expired-ec": ("REP-15", "अवधि समाप्त EC विशेषज्ञ", "unavailable_expiry"),
}


def _current_year():
    return nomination_year(timezone.localdate())


def available_years():
    years = set(UtilisationEntry.objects.values_list("nomination_year", flat=True))
    years.update(ReplacementContribution.objects.values_list("nomination_year", flat=True))
    years.add(_current_year())
    return sorted(years, reverse=True)


def normalise_filters(params):
    years = available_years()
    year = params.get("year", "").strip()
    if year not in years:
        year = _current_year()
    role = params.get("role", "").strip()
    if role not in ROLE_LABELS:
        role = ""
    category = params.get("category", "").strip()
    if category not in Expert.Category.values:
        category = ""
    college = params.get("college", "").strip()
    subject = params.get("subject", "").strip()
    return {
        "year": year,
        "role": role,
        "category": category,
        "college": college,
        "subject": subject,
        "years": years,
        "colleges": Institution.objects.filter(is_active=True).order_by("name"),
        "subjects": Subject.objects.filter(is_active=True).order_by("name"),
    }


def _matches(row, filters):
    return (
        (not filters["role"] or row["role"] == filters["role"])
        and (not filters["category"] or row["category"] == filters["category"])
        and (not filters["college"] or row["college_id"] == filters["college"])
        and (not filters["subject"] or row["subject_id"] == filters["subject"])
    )


def effective_contributions(filters):
    """Return the surviving +1 entries only; reversals are intentionally absent."""
    rows = []
    entries = (
        UtilisationEntry.objects.filter(nomination_year=filters["year"], reversal__isnull=True)
        .select_related(
            "expert",
            "selection__request__institution",
            "selection__request__subject",
        )
        .order_by("locked_at", "expert__sequence")
    )
    for entry in entries:
        request = entry.selection.request
        rows.append(
            {
                "expert_id": str(entry.expert_id),
                "expert": entry.snapshot.get("name") or entry.expert.name,
                "sequence": entry.expert.sequence,
                "category": entry.snapshot.get("category") or entry.expert.category or "",
                "role": entry.role,
                "role_label": ROLE_LABELS.get(entry.role, entry.role),
                "appointment_type": entry.appointment_type,
                "recorded_at": entry.locked_at,
                "college_id": str(request.institution_id),
                "college": request.institution.name,
                "subject_id": str(request.subject_id or ""),
                "subject": request.subject.name if request.subject_id else "—",
                "request_id": str(request.pk),
                "selection_id": str(entry.selection_id),
                "source": "अंतिम लॉक",
            }
        )
    replacements = (
        ReplacementContribution.objects.filter(
            nomination_year=filters["year"], reversal__isnull=True
        )
        .select_related(
            "expert",
            "change__selection__request__institution",
            "change__selection__request__subject",
        )
        .order_by("locked_at", "expert__sequence")
    )
    for entry in replacements:
        request = entry.change.selection.request
        rows.append(
            {
                "expert_id": str(entry.expert_id),
                "expert": entry.expert.name,
                "sequence": entry.expert.sequence,
                "category": entry.expert.category or "",
                "role": entry.role,
                "role_label": ROLE_LABELS.get(entry.role, entry.role),
                "appointment_type": entry.appointment_type,
                "recorded_at": entry.locked_at,
                "college_id": str(request.institution_id),
                "college": request.institution.name,
                "subject_id": str(request.subject_id or ""),
                "subject": request.subject.name if request.subject_id else "—",
                "request_id": str(request.pk),
                "selection_id": str(entry.change.selection_id),
                "source": "पुष्ट प्रतिस्थापन",
            }
        )
    return [row for row in rows if _matches(row, filters)]


def reversals(filters):
    """Expose reversals separately; a reversal is never presented as a negative nomination."""
    items = UtilisationReversal.objects.filter(
        Q(entry__nomination_year=filters["year"])
        | Q(replacement_entry__nomination_year=filters["year"])
    ).select_related(
        "entry__expert",
        "entry__selection__request__institution",
        "entry__selection__request__subject",
        "replacement_entry__expert",
        "replacement_entry__change__selection__request__institution",
        "replacement_entry__change__selection__request__subject",
    )
    rows = []
    for item in items:
        contribution = item.entry or item.replacement_entry
        request = (
            contribution.selection.request
            if item.entry
            else contribution.change.selection.request
        )
        row = {
            "expert_id": str(contribution.expert_id),
            "expert": contribution.expert.name,
            "category": contribution.expert.category or "",
            "role": contribution.role,
            "college_id": str(request.institution_id),
            "subject_id": str(request.subject_id or ""),
            "reversed_at": item.reversed_at,
        }
        if _matches(row, filters):
            rows.append(row)
    return rows


def _lifetime_stats():
    filters = {"year": "", "role": "", "category": "", "college": "", "subject": ""}
    rows = []
    for year in available_years():
        filters["year"] = year
        rows.extend(effective_contributions(filters))
    counts, last = defaultdict(int), {}
    for row in rows:
        counts[row["expert_id"]] += 1
        last[row["expert_id"]] = max(last.get(row["expert_id"], date.min), row["recorded_at"].date())
    return counts, last


def expert_utilisation_rows(filters):
    current = defaultdict(int)
    roles = defaultdict(set)
    for row in effective_contributions(filters):
        current[row["expert_id"]] += 1
        roles[row["expert_id"]].add(row["role_label"])
    lifetime, last = _lifetime_stats()
    appointments = {
        str(item.expert_id): item
        for item in Appointment.objects.filter(is_current=True).select_related("institution")
    }
    rows = []
    for expert in Expert.objects.filter(is_active=True).order_by("sequence"):
        appointment = appointments.get(str(expert.pk))
        if filters["category"] and expert.category != filters["category"]:
            continue
        if filters["subject"] and not expert.subjects.filter(pk=filters["subject"]).exists():
            continue
        rows.append(
            {
                "expert": expert.name,
                "sequence": expert.sequence,
                "category": expert.get_category_display() if expert.category else "—",
                "current": current[str(expert.pk)],
                "lifetime": lifetime[str(expert.pk)],
                "last": last.get(str(expert.pk)),
                "roles": ", ".join(sorted(roles[str(expert.pk)])) or "—",
                "institution": appointment.institution.name if appointment else "सत्यापन शेष",
                "designation": appointment.get_academic_designation_display() if appointment else "सत्यापन शेष",
                "post": appointment.get_administrative_post_display() if appointment else "—",
                "active": "सक्रिय",
            }
        )
    return rows


def dashboard(filters):
    locked = FinalSelection.objects.filter(state=FinalSelection.State.LOCKED)
    locked_request_ids = locked.values_list("request_id", flat=True)
    pending = RequestDraft.objects.filter(
        state__in=[RequestDraft.State.SUBMITTED, RequestDraft.State.OFFERED]
    ).exclude(pk__in=locked_request_ids)
    contributions = effective_contributions(filters)
    expert_rows = expert_utilisation_rows(filters)
    return {
        "cards": [
            ("कुल अनुरोध", RequestDraft.objects.count(), "सभी अनुरोध प्रारूप"),
            ("लंबित अनुरोध", pending.count(), "प्रस्तुत/प्रस्तावित, अभी अंतिम लॉक नहीं"),
            ("लॉक समितियाँ", locked.count(), "VC/Admin द्वारा अंतिम लॉक"),
            (
                "जारी अंतिम पत्र",
                LetterRevision.objects.filter(
                    state=LetterRevision.State.APPROVED, letter__kind=Letter.Kind.FINAL
                )
                .values("source_selection_id")
                .distinct()
                .count(),
                "स्वीकृत अंतिम दस्तावेज",
            ),
            ("सक्रिय विशेषज्ञ", Expert.objects.filter(is_active=True).count(), "निर्देशिका"),
            (
                "SC/ST सक्रिय विशेषज्ञ",
                Expert.objects.filter(is_active=True, category__in=["sc", "st"]).count(),
                "निर्देशिका",
            ),
            (
                "OBC सक्रिय विशेषज्ञ",
                Expert.objects.filter(is_active=True, category="obc").count(),
                "निर्देशिका",
            ),
            (
                "इस वर्ष शून्य उपयोग",
                sum(row["current"] == 0 for row in expert_rows),
                "सक्रिय विशेषज्ञ; केस-विशिष्ट पात्रता का दावा नहीं",
            ),
        ],
        "contribution_count": len(contributions),
        "expert_rows": expert_rows,
    }


def _group(rows, key, label):
    grouped = defaultdict(int)
    for row in rows:
        grouped[row[key]] += 1
    return [{label: value, "नामांकन": count} for value, count in sorted(grouped.items())]


def _effective_members(selection):
    from apps.nominations.services import _current_panel_members

    current = _current_panel_members(selection)
    experts = Expert.objects.in_bulk(item["expert_id"] for item in current.values())
    result = []
    for item in current.values():
        expert = experts[item["expert_id"]]
        member = item["member"]
        result.append(
            {
                "expert": expert,
                "role": item["role"],
                "name": member.snapshot.get("name") if member else expert.name,
                "category": (member.snapshot.get("category") if member else None)
                or expert.category,
            }
        )
    return sorted(result, key=lambda item: (item["role"], item["expert"].sequence))


def report_data(slug, filters):
    report_id, title, kind = REPORTS[slug]
    data = {"id": report_id, "title": title, "slug": slug, "columns": [], "rows": []}
    rows = effective_contributions(filters)
    if kind == "role":
        required_role = {"professors": "professor", "principals": "principal", "vc-nominees": "vc"}[slug]
        rows = [row for row in rows if row["role"] == required_role]
        grouped = defaultdict(lambda: {"नामांकन": 0, "अंतिम नामांकन": None, "भूमिका": ""})
        for row in rows:
            item = grouped[row["expert"]]
            item.update({"विशेषज्ञ": row["expert"], "क्रमांक": row["sequence"], "भूमिका": row["role_label"]})
            item["नामांकन"] += 1
            item["अंतिम नामांकन"] = max(item["अंतिम नामांकन"] or row["recorded_at"].date(), row["recorded_at"].date())
        data["columns"] = ["विशेषज्ञ", "क्रमांक", "भूमिका", "नामांकन", "अंतिम नामांकन"]
        data["rows"] = sorted(grouped.values(), key=lambda item: (-item["नामांकन"], item["क्रमांक"]))
    elif kind == "annual":
        data["columns"] = ["विशेषज्ञ", "क्रमांक", "श्रेणी", "नामांकन", "अंतिम नामांकन"]
        grouped = defaultdict(lambda: {"नामांकन": 0, "अंतिम नामांकन": None})
        for row in rows:
            item = grouped[row["expert_id"]]
            item.update({"विशेषज्ञ": row["expert"], "क्रमांक": row["sequence"], "श्रेणी": row["category"] or "—"})
            item["नामांकन"] += 1
            item["अंतिम नामांकन"] = max(item["अंतिम नामांकन"] or row["recorded_at"].date(), row["recorded_at"].date())
        data["rows"] = sorted(grouped.values(), key=lambda item: (-item["नामांकन"], item["क्रमांक"]))
    elif kind == "subjects":
        data["columns"] = ["विषय", "नामांकन"]
        data["rows"] = _group(rows, "subject", "विषय")
    elif kind == "months":
        data["columns"] = ["माह", "प्रभावी नामांकन", "उलटे योगदान"]
        for row in rows:
            row["recorded_month"] = row["recorded_at"].strftime("%Y-%m")
        grouped = defaultdict(lambda: {"प्रभावी नामांकन": 0, "उलटे योगदान": 0})
        for row in rows:
            grouped[row["recorded_month"]]["माह"] = row["recorded_month"]
            grouped[row["recorded_month"]]["प्रभावी नामांकन"] += 1
        for row in reversals(filters):
            month = row["reversed_at"].strftime("%Y-%m")
            grouped[month]["माह"] = month
            grouped[month]["उलटे योगदान"] += 1
        data["rows"] = [grouped[key] for key in sorted(grouped)]
    elif kind == "not_nominated":
        data["columns"] = ["विशेषज्ञ", "क्रमांक", "श्रेणी", "संस्था", "पदनाम"]
        data["rows"] = [
            {key: row[key] for key in ["expert", "sequence", "category", "institution", "designation"]}
            for row in expert_utilisation_rows(filters)
            if row["current"] == 0
        ]
    elif kind == "maximum":
        expert_rows = expert_utilisation_rows(filters)
        highest = max((row["current"] for row in expert_rows), default=0)
        data["columns"] = ["विशेषज्ञ", "क्रमांक", "श्रेणी", "नामांकन"]
        data["rows"] = [
            {"विशेषज्ञ": row["expert"], "क्रमांक": row["sequence"], "श्रेणी": row["category"], "नामांकन": row["current"]}
            for row in expert_rows
            if row["current"] == highest and highest > 0
        ]
    elif kind == "committees":
        selections = (
            FinalSelection.objects.filter(state=FinalSelection.State.LOCKED)
            .select_related("request__institution", "request__subject")
            .order_by("-locked_at")
        )
        data["columns"] = ["महाविद्यालय", "पद", "विषय", "लॉक तिथि", "अंतिम संरचना", "पुष्ट परिवर्तन"]
        data["rows"] = [
            {
                "महाविद्यालय": item.request.institution.name,
                "पद": item.request.get_appointment_type_display(),
                "विषय": item.request.subject.name if item.request.subject_id else "—",
                "लॉक तिथि": item.locked_at.date() if item.locked_at else "—",
                "अंतिम संरचना": "; ".join(
                    f"{ROLE_LABELS.get(member['role'], member['role'])}: {member['name']}"
                    for member in _effective_members(item)
                ),
                "पुष्ट परिवर्तन": item.changes.filter(state=PanelChange.State.CONFIRMED).count(),
            }
            for item in selections
            if (not filters["college"] or str(item.request.institution_id) == filters["college"])
            and (not filters["subject"] or str(item.request.subject_id) == filters["subject"])
        ]
    elif kind.startswith("representation_"):
        target = "obc" if kind == "representation_obc" else "scst"
        categories = {"obc"} if target == "obc" else {"sc", "st"}
        data["columns"] = ["महाविद्यालय", "विशेषज्ञ", "भूमिका", "श्रेणी", "लॉक तिथि"]
        selections = FinalSelection.objects.filter(state=FinalSelection.State.LOCKED).select_related(
            "request__institution", "request__subject"
        )
        for selection in selections:
            if not selection.locked_at or nomination_year(selection.locked_at.date()) != filters["year"]:
                continue
            if filters["college"] and str(selection.request.institution_id) != filters["college"]:
                continue
            if filters["subject"] and str(selection.request.subject_id) != filters["subject"]:
                continue
            for member in _effective_members(selection):
                category = member["category"]
                if member["role"] == "vc" or category not in categories:
                    continue
                if filters["role"] and member["role"] != filters["role"]:
                    continue
                if filters["category"] and category != filters["category"]:
                    continue
                data["rows"].append(
                    {
                        "महाविद्यालय": selection.request.institution.name,
                        "विशेषज्ञ": member["name"],
                        "भूमिका": ROLE_LABELS.get(member["role"], member["role"]),
                        "श्रेणी": category.upper(),
                        "लॉक तिथि": selection.locked_at.date() if selection.locked_at else "—",
                    }
                )
    elif kind == "cancellations":
        changes = PanelChange.objects.filter(
            change_type=PanelChange.Type.CANCELLATION, state=PanelChange.State.CONFIRMED
        ).select_related("selection__request__institution", "confirmed_by")
        data["columns"] = ["महाविद्यालय", "कारण", "उलटे योगदान", "पुष्ट तिथि", "पुष्ट करने वाले"]
        data["rows"] = [
            {
                "महाविद्यालय": change.selection.request.institution.name,
                "कारण": change.reason,
                "उलटे योगदान": change.reversals.count(),
                "पुष्ट तिथि": change.confirmed_at.date() if change.confirmed_at else "—",
                "पुष्ट करने वाले": str(change.confirmed_by or "—"),
            }
            for change in changes
        ]
    elif kind == "replacements":
        changes = PanelChange.objects.filter(
            change_type=PanelChange.Type.REPLACEMENT, state=PanelChange.State.CONFIRMED
        ).select_related("selection__request__institution", "outgoing_expert", "replacement_expert", "confirmed_by")
        data["columns"] = ["महाविद्यालय", "हटाए गए विशेषज्ञ", "प्रतिस्थापन", "भूमिका", "कारण", "गणना प्रभाव", "पुष्ट तिथि"]
        data["rows"] = [
            {
                "महाविद्यालय": change.selection.request.institution.name,
                "हटाए गए विशेषज्ञ": change.outgoing_expert.name if change.outgoing_expert_id else "—",
                "प्रतिस्थापन": change.replacement_expert.name if change.replacement_expert_id else "—",
                "भूमिका": ROLE_LABELS.get(change.role, change.role),
                "कारण": change.reason,
                "गणना प्रभाव": "हटाया -1; प्रतिस्थापन +1",
                "पुष्ट तिथि": change.confirmed_at.date() if change.confirmed_at else "—",
            }
            for change in changes
        ]
    else:
        data["unavailable"] = (
            "मैनुअल विचलन के लिए कोई अधिकृत ओवरराइड रिकॉर्ड नहीं है।"
            if kind == "unavailable_deviations"
            else "EC विशेषज्ञ निर्देशिका में वैधता-अवधि का नियंत्रित रिकॉर्ड अभी परिभाषित नहीं है।"
        )
    return data
