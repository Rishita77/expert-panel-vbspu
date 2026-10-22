"""Display aggregate explanations from saved evidence, without exposing candidate lists."""
from collections import Counter

from django.utils.translation import gettext as _

from .engine import ROLE_LABELS


def allocation_diagnostics(snapshot):
    policy = snapshot.get("policy", {})
    required = {"vc": policy.get("vc_nominees", 1), "principal": policy.get("principals", 1), "professor": policy.get("professors", 5), "obc": 1, "scst": 1}
    roles = {item["key"]: item for item in snapshot.get("roles", [])}
    blockers, summaries = [], []
    for key in ("vc", "principal", "professor", "obc", "scst"):
        role = roles.get(key)
        label = _(ROLE_LABELS[key])
        if role is None:
            if key in {"obc", "scst"} and blockers:
                summaries.append({"label": label, "message": _("जाँच नहीं हुई: पहले %(roles)s की समस्या दूर करें। यह श्रेणी उम्मीदवारों की कमी का निष्कर्ष नहीं है।") % {"roles": ", ".join(blockers)}, "reasons": []})
            continue
        rows = role.get("rows", [])
        eligible = sum(row.get("rank") is not None for row in rows)
        selected = sum(bool(row.get("selected")) for row in rows)
        count = required[key]
        if selected >= count:
            continue
        message = _("आवश्यक: %(required)s; योग्य उपलब्ध: %(eligible)s; चयनित: %(selected)s।") % {"required": count, "eligible": eligible, "selected": selected}
        if blockers:
            message += " " + _("चयन रुका है: पहले %(roles)s की समस्या दूर करें।") % {"roles": ", ".join(blockers)}
        relevant = rows
        if key in {"obc", "scst"}:
            categories = {"obc"} if key == "obc" else {"sc", "st"}
            relevant = [row for row in rows if row.get("category") in categories]
        reasons = Counter(reason for row in relevant for reason in set(row.get("reasons", [])))
        summaries.append({"label": label, "message": message, "reasons": [{"text": _(reason), "count": total} for reason, total in sorted(reasons.items())], "empty": not relevant})
        if key in {"vc", "principal", "professor"}:
            # A source/history error can block selection even with enough eligible rows.
            if eligible < count or not blockers:
                blockers.append(label)
    return summaries
