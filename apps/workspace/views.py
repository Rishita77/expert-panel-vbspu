from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from apps.nominations.policies import POLICIES

from .forms import IntakePreviewForm


@require_GET
def home(request):
    return render(request, "workspace/home.html", {"section": "home"})


@require_http_methods(["GET", "POST"])
def intake(request):
    form = IntakePreviewForm(request.POST if request.method == "POST" else None)
    context = {"section": "intake", "form": form}
    if request.method == "POST":
        if request.POST.get("_action") == "edit":
            return render(request, "workspace/intake.html", context)
        if form.is_valid():
            context["rows"] = form.display_rows()
            context["policy"] = POLICIES.get(form.cleaned_data.get("appointment_type"))
            return render(request, "workspace/intake_preview.html", context)
        context["error_summary"] = True
    return render(request, "workspace/intake.html", context)


@require_GET
def policies(request):
    key = request.GET.get("type", "principal")
    if key not in POLICIES:
        raise Http404("Unknown appointment type")
    context = {"section": "policies", "policies": POLICIES.values(), "policy": POLICIES[key]}
    return render(request, "workspace/policies.html", context)


@require_GET
def health(request):
    # Liveness only: never report database/auth readiness or environment details.
    return JsonResponse({"status": "ok"})
