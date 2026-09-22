import csv

from django.http import Http404, HttpResponse
from django.shortcuts import render

from apps.accounts.access import permitted
from apps.accounts.models import Role

from .services import REPORTS, dashboard, normalise_filters, report_data


@permitted(Role.REVIEWER, Role.VC)
def home(request):
    filters = normalise_filters(request.GET)
    return render(
        request,
        "reporting/home.html",
        {"filters": filters, "dashboard": dashboard(filters), "reports": REPORTS},
    )


@permitted(Role.REVIEWER, Role.VC)
def report(request, slug):
    if slug not in REPORTS:
        raise Http404
    filters = normalise_filters(request.GET)
    return render(
        request,
        "reporting/report.html",
        {"filters": filters, "report": report_data(slug, filters), "reports": REPORTS},
    )


def _safe_cell(value):
    value = "" if value is None else str(value)
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


@permitted(Role.REVIEWER, Role.VC)
def export_csv(request, slug):
    if slug not in REPORTS:
        raise Http404
    data = report_data(slug, normalise_filters(request.GET))
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{slug}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    if data.get("unavailable"):
        writer.writerow([data["title"]])
        writer.writerow([data["unavailable"]])
    else:
        writer.writerow(data["columns"])
        for row in data["rows"]:
            writer.writerow([_safe_cell(row.get(column, "")) for column in data["columns"]])
    return response
