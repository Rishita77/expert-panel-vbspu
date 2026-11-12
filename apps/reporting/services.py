from django.utils.translation import gettext, gettext_lazy
"""One read-only reporting path over the immutable nomination ledger."""

from collections import defaultdict
from datetime import date

from django.db.models import Q
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.cases.models import RequestDraft
from apps.experts.models import Appointment, Expert
from apps.institutions.models import Institution, Subject
from apps.nominations.engine import ROLE_LABELS, nomination_year
from apps.nominations.models import (
    FinalSelection,
    FinalRelease,
    Letter,
    LetterRevision,
    PanelChange,
    ReplacementContribution,
    UtilisationEntry,
    UtilisationReversal,
)


REPORTS = {
    "professors": ("REP-01", gettext_lazy("प्रोफेसर-वार नामांकन"), "role"),
    "principals": ("REP-02", gettext_lazy("प्राचार्य-वार नामांकन"), "role"),
    "vc-nominees": ("REP-03", gettext_lazy("कुलपति नामित उपयोग"), "role"),
    "committees": ("REP-04", gettext_lazy("महाविद्यालय-वार चयन समितियाँ"), "committees"),
    "subjects": ("REP-05", gettext_lazy("विषय-वार नामांकन"), "subjects"),
    "months": ("REP-06", gettext_lazy("माह-वार नामांकन"), "months"),
    "annual-utilisation": ("REP-07", gettext_lazy("जुलाई-जून वार्षिक उपयोग"), "annual"),
    "scst-representation": ("REP-08", gettext_lazy("SC/ST प्रतिनिधित्व"), "representation_scst"),
    "obc-representation": ("REP-09", gettext_lazy("OBC प्रतिनिधित्व"), "representation_obc"),
    "not-nominated": ("REP-10", gettext_lazy("वर्ष में नामांकित नहीं हुए विशेषज्ञ"), "not_nominated"),
    "maximum-nominations": ("REP-11", gettext_lazy("सर्वाधिक नामांकित विशेषज्ञ"), "maximum"),
    "cancellations": ("REP-12", gettext_lazy("रद्द नामांकन"), "cancellations"),
    "replacements": ("REP-13", gettext_lazy("प्रतिस्थापन विशेषज्ञ"), "replacements"),
    "manual-deviations": ("REP-14", gettext_lazy("मान्य मैनुअल विचलन"), "deviations"),
    "expired-ec": ("REP-15", gettext_lazy("अवधि समाप्त EC विशेषज्ञ"), "unavailable_expiry"),
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
                "source": gettext_lazy("अंतिम लॉक"),
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
                "source": gettext_lazy("पुष्ट प्रतिस्थापन"),
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


def directory_details(ids):
    appointments = {
        item.expert_id: item for item in Appointment.objects.filter(
            is_current=True, expert_id__in=ids
        ).select_related("institution")
    }
    details = {}
    for expert in Expert.objects.filter(pk__in=ids).prefetch_related("subjects"):
        home = appointments.get(expert.pk)
        details[str(expert.pk)] = {
            "institution": home.institution.name if home else "—",
            "designation": home.get_academic_designation_display() if home else "—",
            "subjects": ", ".join(s.name for s in expert.subjects.all()) or "—",
        }
    return details


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
    for expert in Expert.objects.filter(is_active=True).prefetch_related("subjects").order_by("sequence"):
        appointment = appointments.get(str(expert.pk))
        if filters["category"] and expert.category != filters["category"]:
            continue
        if filters["subject"] and not any(str(s.pk) == filters["subject"] for s in expert.subjects.all()):
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
                "institution": appointment.institution.name if appointment else gettext_lazy("सत्यापन शेष"),
                "designation": appointment.get_academic_designation_display() if appointment else gettext_lazy("सत्यापन शेष"),
                "subjects": ", ".join(s.name for s in expert.subjects.all()) or "—",
                "post": appointment.get_administrative_post_display() if appointment else "—",
                "active": gettext_lazy("सक्रिय"),
            }
        )
    return rows


def overall_cards():
    locked = FinalSelection.objects.filter(state=FinalSelection.State.LOCKED)
    pending = RequestDraft.objects.filter(
        state__in=[RequestDraft.State.SUBMITTED, RequestDraft.State.REVIEWED, RequestDraft.State.OFFERED]
    ).exclude(pk__in=locked.values("request_id"))
    return [
        (gettext_lazy("कुल अनुरोध"), RequestDraft.objects.count()),
        (gettext_lazy("लंबित अनुरोध"), pending.count()),
        (gettext_lazy("लॉक समितियाँ"), locked.count()),
        (gettext_lazy("जारी अंतिम पत्र"), FinalRelease.objects.count()),
        (gettext_lazy("सक्रिय विशेषज्ञ"), Expert.objects.filter(is_active=True).count()),
    ]


def dashboard(filters):
    # Every displayed count and date comes from the same filtered ledger.
    contributions = effective_contributions(filters)
    details = directory_details({row["expert_id"] for row in contributions})
    grouped = {}
    for row in contributions:
        key = row["expert_id"]
        item = grouped.setdefault(key, {
            "expert": row["expert"], "sequence": row["sequence"],
            "category": Expert.Category(row["category"]).label if row["category"] else "—",
            **details.get(key, {"institution": "—", "designation": "—", "subjects": "—"}),
            "current": 0, "last": None,
        })
        item["current"] += 1
        day = row["recorded_at"].date()
        item["last"] = max(item["last"] or day, day)
    return {"expert_rows": sorted(grouped.values(), key=lambda row: row["sequence"])}


def _group(rows, key, label):
    grouped = defaultdict(int)
    for row in rows:
        grouped[row[key]] += 1
    return [{label: value, gettext_lazy("नामांकन"): count} for value, count in sorted(grouped.items())]


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
        grouped = defaultdict(lambda: {gettext_lazy("नामांकन"): 0, gettext_lazy("अंतिम नामांकन"): None, gettext_lazy("भूमिका"): ""})
        details = directory_details({row["expert_id"] for row in rows})
        profile_columns = [gettext_lazy("वर्तमान संस्था"), gettext_lazy("वर्तमान शैक्षणिक पदनाम"), gettext_lazy("वर्तमान विषय")]
        for row in rows:
            item = grouped[row["expert_id"]]
            profile = details[row["expert_id"]]
            item.update(zip(profile_columns, (profile["institution"], profile["designation"], profile["subjects"])))
            item.update({gettext_lazy("विशेषज्ञ"): row["expert"], gettext_lazy("क्रमांक"): row["sequence"], gettext_lazy("भूमिका"): row["role_label"]})
            item[gettext_lazy("नामांकन")] += 1
            item[gettext_lazy("अंतिम नामांकन")] = max(item[gettext_lazy("अंतिम नामांकन")] or row["recorded_at"].date(), row["recorded_at"].date())
        data["columns"] = [gettext_lazy("विशेषज्ञ"), gettext_lazy("क्रमांक"), *profile_columns, gettext_lazy("भूमिका"), gettext_lazy("नामांकन"), gettext_lazy("अंतिम नामांकन")]
        data["rows"] = sorted(grouped.values(), key=lambda item: (-item[gettext_lazy("नामांकन")], item[gettext_lazy("क्रमांक")]))
    elif kind == "annual":
        data["columns"] = [gettext_lazy("विशेषज्ञ"), gettext_lazy("क्रमांक"), gettext_lazy("श्रेणी"), gettext_lazy("नामांकन"), gettext_lazy("अंतिम नामांकन")]
        grouped = defaultdict(lambda: {gettext_lazy("नामांकन"): 0, gettext_lazy("अंतिम नामांकन"): None})
        for row in rows:
            item = grouped[row["expert_id"]]
            item.update({gettext_lazy("विशेषज्ञ"): row["expert"], gettext_lazy("क्रमांक"): row["sequence"], gettext_lazy("श्रेणी"): row["category"] or "—"})
            item[gettext_lazy("नामांकन")] += 1
            item[gettext_lazy("अंतिम नामांकन")] = max(item[gettext_lazy("अंतिम नामांकन")] or row["recorded_at"].date(), row["recorded_at"].date())
        data["rows"] = sorted(grouped.values(), key=lambda item: (-item[gettext_lazy("नामांकन")], item[gettext_lazy("क्रमांक")]))
    elif kind == "subjects":
        data["columns"] = [gettext_lazy("विषय"), gettext_lazy("नामांकन")]
        data["rows"] = _group(rows, "subject", gettext_lazy("विषय"))
    elif kind == "months":
        data["columns"] = [gettext_lazy("माह"), gettext_lazy("प्रभावी नामांकन"), gettext_lazy("उलटे योगदान")]
        for row in rows:
            row["recorded_month"] = row["recorded_at"].strftime("%Y-%m")
        grouped = defaultdict(lambda: {gettext_lazy("प्रभावी नामांकन"): 0, gettext_lazy("उलटे योगदान"): 0})
        for row in rows:
            grouped[row["recorded_month"]][gettext_lazy("माह")] = row["recorded_month"]
            grouped[row["recorded_month"]][gettext_lazy("प्रभावी नामांकन")] += 1
        for row in reversals(filters):
            month = row["reversed_at"].strftime("%Y-%m")
            grouped[month][gettext_lazy("माह")] = month
            grouped[month][gettext_lazy("उलटे योगदान")] += 1
        data["rows"] = [grouped[key] for key in sorted(grouped)]
    elif kind == "not_nominated":
        data["columns"] = [gettext_lazy("विशेषज्ञ"), gettext_lazy("क्रमांक"), gettext_lazy("श्रेणी"), gettext_lazy("संस्था"), gettext_lazy("पदनाम")]
        data["rows"] = [
            {key: row[key] for key in ["expert", "sequence", "category", "institution", "designation"]}
            for row in expert_utilisation_rows(filters)
            if row["current"] == 0
        ]
    elif kind == "maximum":
        expert_rows = expert_utilisation_rows(filters)
        highest = max((row["current"] for row in expert_rows), default=0)
        data["columns"] = [gettext_lazy("विशेषज्ञ"), gettext_lazy("क्रमांक"), gettext_lazy("श्रेणी"), gettext_lazy("नामांकन")]
        data["rows"] = [
            {gettext_lazy("विशेषज्ञ"): row["expert"], gettext_lazy("क्रमांक"): row["sequence"], gettext_lazy("श्रेणी"): row["category"], gettext_lazy("नामांकन"): row["current"]}
            for row in expert_rows
            if row["current"] == highest and highest > 0
        ]
    elif kind == "committees":
        selections = (
            FinalSelection.objects.filter(state=FinalSelection.State.LOCKED)
            .select_related("request__institution", "request__subject")
            .order_by("-locked_at")
        )
        data["columns"] = [gettext_lazy("महाविद्यालय"), gettext_lazy("पद"), gettext_lazy("विषय"), gettext_lazy("लॉक तिथि"), gettext_lazy("अंतिम संरचना"), gettext_lazy("पुष्ट परिवर्तन")]
        data["rows"] = [
            {
                gettext_lazy("महाविद्यालय"): item.request.institution.name,
                gettext_lazy("पद"): item.request.get_appointment_type_display(),
                gettext_lazy("विषय"): item.request.subject.name if item.request.subject_id else "—",
                gettext_lazy("लॉक तिथि"): item.locked_at.date() if item.locked_at else "—",
                gettext_lazy("अंतिम संरचना"): "; ".join(
                    f"{gettext(ROLE_LABELS.get(member['role'], member['role']))}: {member['name']}"
                    for member in _effective_members(item)
                ),
                gettext_lazy("पुष्ट परिवर्तन"): item.changes.filter(state=PanelChange.State.CONFIRMED).count(),
            }
            for item in selections
            if (not filters["college"] or str(item.request.institution_id) == filters["college"])
            and (not filters["subject"] or str(item.request.subject_id) == filters["subject"])
        ]
    elif kind.startswith("representation_"):
        target = "obc" if kind == "representation_obc" else "scst"
        categories = {"obc"} if target == "obc" else {"sc", "st"}
        data["columns"] = [gettext_lazy("महाविद्यालय"), gettext_lazy("विशेषज्ञ"), gettext_lazy("भूमिका"), gettext_lazy("श्रेणी"), gettext_lazy("लॉक तिथि")]
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
                        gettext_lazy("महाविद्यालय"): selection.request.institution.name,
                        gettext_lazy("विशेषज्ञ"): member["name"],
                        gettext_lazy("भूमिका"): gettext(ROLE_LABELS.get(member["role"], member["role"])),
                        gettext_lazy("श्रेणी"): category.upper(),
                        gettext_lazy("लॉक तिथि"): selection.locked_at.date() if selection.locked_at else "—",
                    }
                )
    elif kind == "cancellations":
        changes = PanelChange.objects.filter(
            change_type=PanelChange.Type.CANCELLATION, state=PanelChange.State.CONFIRMED
        ).select_related("selection__request__institution", "confirmed_by")
        data["columns"] = [gettext_lazy("महाविद्यालय"), gettext_lazy("कारण"), gettext_lazy("उलटे योगदान"), gettext_lazy("पुष्ट तिथि"), gettext_lazy("पुष्ट करने वाले")]
        data["rows"] = [
            {
                gettext_lazy("महाविद्यालय"): change.selection.request.institution.name,
                gettext_lazy("कारण"): change.reason,
                gettext_lazy("उलटे योगदान"): change.reversals.count(),
                gettext_lazy("पुष्ट तिथि"): change.confirmed_at.date() if change.confirmed_at else "—",
                gettext_lazy("पुष्ट करने वाले"): str(change.confirmed_by or "—"),
            }
            for change in changes
        ]
    elif kind == "deviations":
        columns = [gettext_lazy("स्थिति"), gettext_lazy("भूमिका"), gettext_lazy("अनुशंसित"),
                   gettext_lazy("चयनित विशेषज्ञ"), gettext_lazy("कारण"), gettext_lazy("दिनांक")]
        data["columns"] = columns
        events = AuditEvent.objects.filter(
            action__in=["allocation.proposal_replaced", "panel_change.replacement_drafted"],
            after__manual=True, after__year=filters["year"],
        )
        for event in events:
            facts = event.after
            if _matches(facts, filters):
                stage = gettext_lazy("संशोधित प्रस्ताव") if event.action == "allocation.proposal_replaced" else gettext_lazy("प्रतिस्थापन प्रारूप")
                data["rows"].append(dict(zip(columns, (stage, gettext(ROLE_LABELS[facts["role"]]),
                    facts["recommended_name"], facts["chosen_name"], event.reason, event.occurred_at.date()))))
    elif kind == "replacements":
        changes = PanelChange.objects.filter(
            change_type=PanelChange.Type.REPLACEMENT, state=PanelChange.State.CONFIRMED
        ).select_related("selection__request__institution", "outgoing_expert", "replacement_expert", "confirmed_by")
        data["columns"] = [gettext_lazy("महाविद्यालय"), gettext_lazy("हटाए गए विशेषज्ञ"), gettext_lazy("प्रतिस्थापन"), gettext_lazy("भूमिका"), gettext_lazy("कारण"), gettext_lazy("गणना प्रभाव"), gettext_lazy("पुष्ट तिथि")]
        data["rows"] = [
            {
                gettext_lazy("महाविद्यालय"): change.selection.request.institution.name,
                gettext_lazy("हटाए गए विशेषज्ञ"): change.outgoing_expert.name if change.outgoing_expert_id else "—",
                gettext_lazy("प्रतिस्थापन"): change.replacement_expert.name if change.replacement_expert_id else "—",
                gettext_lazy("भूमिका"): gettext(ROLE_LABELS.get(change.role, change.role)),
                gettext_lazy("कारण"): change.reason,
                gettext_lazy("गणना प्रभाव"): gettext_lazy("हटाया -1; प्रतिस्थापन +1"),
                gettext_lazy("पुष्ट तिथि"): change.confirmed_at.date() if change.confirmed_at else "—",
            }
            for change in changes
        ]
    else:
        data["unavailable"] = gettext_lazy("EC विशेषज्ञ निर्देशिका में वैधता-अवधि का नियंत्रित रिकॉर्ड अभी परिभाषित नहीं है।")
    return data
