"""Fresh-start nomination history and later locked final nominations."""

from datetime import date

from django.conf import settings

from .engine import History, nomination_year
from .models import ReplacementContribution, UtilisationEntry


def fresh_start_date():
    return getattr(settings, "NOMINATION_FRESH_START_DATE", date(2026, 9, 16))


def verified_history(expert_ids, allocation_date):
    """Every expert starts at zero; only locks after the agreed start count."""
    ids = {str(expert_id) for expert_id in expert_ids}
    year = nomination_year(allocation_date)
    values = {expert_id: [] for expert_id in ids}
    start_date = fresh_start_date()
    entries = UtilisationEntry.objects.filter(
        expert_id__in=ids,
        locked_at__date__gte=start_date,
        reversal__isnull=True,
    ).values("expert_id", "nomination_year", "locked_at")
    replacements = ReplacementContribution.objects.filter(
        expert_id__in=ids,
        locked_at__date__gte=start_date,
        reversal__isnull=True,
    ).values("expert_id", "nomination_year", "locked_at")
    for row in entries.union(replacements):
        values[str(row["expert_id"])].append(row)
    result = {}
    for expert_id, rows in values.items():
        annual_count = sum(row["nomination_year"] == year for row in rows)
        last = max(
            (row["locked_at"].date() for row in rows),
            default=None,
        )
        result[expert_id] = History(annual_count, last, verified_never=last is None)
    return result
