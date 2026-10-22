"""Pure, deterministic allocation. SRS references accompany each rule boundary.

No database, clock, pending-offer weight, counter mutation or approval side effect.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from .policies import POLICIES

ROLE_LABELS = {
    "vc": "कुलपति नामित",
    "principal": "प्राचार्य",
    "professor": "प्रोफेसर",
    "scst": "अतिरिक्त SC/ST",
    "obc": "अतिरिक्त OBC",
}


@dataclass(frozen=True)
class History:
    annual_count: int
    last_nomination: date | None
    verified_never: bool = False

    def valid(self, at_date):
        return (
            type(self.annual_count) is int
            and self.annual_count >= 0
            and (
                (self.verified_never and self.last_nomination is None and self.annual_count == 0)
                or (
                    not self.verified_never
                    and isinstance(self.last_nomination, date)
                    and self.last_nomination <= at_date
                )
            )
        )


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    sequence: int
    category: str
    reasons: tuple[str, ...] = ()
    history: History | None = None
    verified: bool = False


def nomination_year(at_date):
    """SRS 10/16: current July–June year at allocation; DEC-034 date basis."""
    start = at_date.year if at_date.month >= 7 else at_date.year - 1
    return f"{start}-{start + 1}"


def rank_key(candidate):
    """SRS 10/11/14/15/29 + DEC-027/034: common count, lifetime date, sequence."""
    h = candidate.history
    return h.annual_count, h.last_nomination or date.min, candidate.sequence


def allocate(appointment_type, candidates, at_date, source_errors=None):
    policy = POLICIES[appointment_type]
    source_errors = source_errors or {}
    result = {
        "policy": policy.snapshot(),
        "year": nomination_year(at_date),
        "allocation_date": at_date.isoformat(),
        "seats": [],
        "roles": [],
        "issues": [],
        "representation": {},
        "complete": False,
    }
    used = set()
    verified = True

    def fill(role, count, can_commit=True):
        nonlocal verified
        rows = []
        eligible = []
        errors = list(source_errors.get(role, ()))
        seen = set()
        for person in candidates.get(role, ()):
            # SRS 26: membership duplication cannot create duplicate people.
            if person.id in seen:
                continue
            seen.add(person.id)
            reasons = list(person.reasons)
            if person.id in used:
                reasons.append("इसी पैनल की दूसरी भूमिका में चयनित — दोहराव वर्जित (SRS 26)।")
            h = person.history
            row = {
                "id": person.id,
                "name": person.name,
                "sequence": person.sequence,
                "category": person.category,
                "reasons": reasons,
                "count": h.annual_count if h else None,
                "last": h.last_nomination.isoformat() if h and h.last_nomination else None,
                "never": bool(h and h.verified_never),
                "selected": False,
                "rank": None,
                "verified": person.verified,
            }
            rows.append(row)
            if not reasons:
                if h is None or not h.valid(at_date):
                    row["reasons"].append("नामांकन इतिहास अपूर्ण / असत्यापित है; शून्य नहीं माना गया।")
                    errors.append("योग्य उम्मीदवारों का सत्यापित इतिहास आवश्यक है।")
                else:
                    eligible.append((person, row))
        eligible.sort(key=lambda pair: rank_key(pair[0]))
        for position, (_, row) in enumerate(eligible, 1):
            row["rank"] = position
        if len(eligible) < count:
            errors.append(f"{ROLE_LABELS[role]}: {count} आवश्यक, {len(eligible)} योग्य उपलब्ध।")
        success = not errors
        if success and can_commit:
            for person, row in eligible[:count]:
                row["selected"] = True
                used.add(person.id)
                verified = verified and person.verified
                result["seats"].append({**row, "role": role, "label": ROLE_LABELS[role]})
        elif success:
            errors.append("पूर्व आवश्यक भूमिका अपूर्ण है; यह अनुशंसा अभी प्रस्तावित पैनल का भाग नहीं है।")
        result["issues"].extend(f"{ROLE_LABELS[role]}: {e}" for e in dict.fromkeys(errors))
        rows.sort(key=lambda row: (row["rank"] is None, row["rank"] or 0, row["sequence"]))
        result["roles"].append({"key": role, "label": ROLE_LABELS[role], "rows": rows})
        return success

    # VC-first decision: later role diagnostics remain recorded if an earlier
    # component fails, but cannot be presented as a committed offered panel.
    vc_ok = fill("vc", policy.vc_nominees)
    principal_ok = fill("principal", policy.principals, can_commit=vc_ok)
    professors_ok = fill("professor", policy.professors, can_commit=vc_ok and principal_ok)
    # SRS 6: representation checks the main six, never the VC nominee.
    if not (principal_ok and professors_ok and vc_ok):
        result["representation"] = {"scst": "मुख्य पैनल अपूर्ण", "obc": "मुख्य पैनल अपूर्ण"}
    else:
        categories = {s["category"] for s in result["seats"] if s["role"] != "vc"}
        for role, present in [
            ("scst", bool(categories & {"sc", "st"})),
            ("obc", "obc" in categories),
        ]:
            if present:
                result["representation"][role] = "मुख्य छह में प्रतिनिधित्व"
            else:
                ok = fill(role, 1)
                result["representation"][role] = "अतिरिक्त विशेषज्ञ" if ok else "प्रतिनिधित्व अपूर्ण"
    result["complete"] = not result["issues"]
    result["checks_verified"] = verified
    return result


def demonstration(at_date, appointment_type="principal", scenario="standard"):
    """Isolated synthetic facts: never assign made-up history to university masters."""

    def person(i, category="general", reasons=()):
        return Candidate(
            str(i), f"प्रदर्शन विशेषज्ञ {i}", i, category, reasons, History(0, None, True), True
        )

    pools = {
        "vc": [person(1)],
        "principal": [person(2)],
        "professor": [
            person(3, reasons=("अपने महाविद्यालय के विशेषज्ञ — वर्जित।",)),
            *[person(i) for i in range(4, 10)],
        ],
        "scst": [person(10, "sc")],
        "obc": [person(11, "obc")],
    }
    if appointment_type == "subject_expert":
        pools["vc"].append(person(12))
    if scenario == "fairness":
        pools["professor"] = [
            Candidate(
                str(i),
                f"प्रदर्शन विशेषज्ञ {i}",
                i,
                "general",
                (),
                History(count, at_date - timedelta(days=days)),
                True,
            )
            for i, count, days in [
                (4, 2, 10),
                (5, 1, 2),
                (6, 1, 5),
                (7, 1, 5),
                (8, 0, 400),
                (9, 3, 1),
            ]
        ]
    elif scenario == "shortage":
        pools["professor"] = pools["professor"][:4]
    result = allocate(appointment_type, pools, at_date)
    result["synthetic"] = True
    result["scenario"] = scenario
    return result
