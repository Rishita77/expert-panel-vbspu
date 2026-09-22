from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.access import permitted, roles_for
from apps.accounts.models import Role
from apps.audit.models import AuditEvent
from apps.cases.services import EditConflict

from .forms import (
    AppointmentForm,
    CheckContextForm,
    ExpertForm,
)
from .models import Appointment, Expert
from .services import save_appointment, save_expert

READ = (Role.MASTER, Role.PROCESSOR, Role.REVIEWER, Role.VC)
REGISTRY = {
    "experts": (Expert, ExpertForm, "विशेषज्ञ"),
    "appointments": (Appointment, AppointmentForm, "संस्था / पद इतिहास"),
}


def spec(kind):
    from django.http import Http404

    if kind not in REGISTRY:
        raise Http404
    return REGISTRY[kind]


def parent_url(kind, obj):
    if kind == "appointments":
        return reverse("expert_detail", args=["experts", obj.expert_id])
    return reverse("expert_detail", args=[kind, obj.pk])


@permitted(*READ)
@require_GET
def listing(request, kind):
    model, _, title = spec(kind)
    if kind != "experts":
        from django.http import Http404

        raise Http404
    query = request.GET.get("q", "").strip()[:200]
    rows = model.objects.all()
    if query:
        if kind == "experts":
            rows = rows.filter(
                Q(name__icontains=query) | Q(appointments__institution__name__icontains=query)
            ).distinct()
    return render(
        request,
        "experts/list.html",
        {
            "kind": kind,
            "title": title,
            "query": query,
            "page": Paginator(rows, 25).get_page(request.GET.get("page")),
        },
    )


@permitted(Role.MASTER)
@require_http_methods(["GET", "POST"])
def edit(request, kind, pk=None, parent=None):
    model, form_class, title = spec(kind)
    obj = get_object_or_404(model, pk=pk) if pk else model()
    home = None
    if kind == "appointments":
        home = get_object_or_404(Expert, pk=parent or obj.expert_id)
        if pk and obj.expert_id != home.pk:
            from django.http import Http404

            raise Http404
        obj.expert = home
    form = form_class(request.POST if request.method == "POST" else None, instance=obj)
    if kind == "appointments":
        form.fields["expert_revision"].initial = home.revision
    status = 200
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            if kind == "experts":
                saved = save_expert(request.user, data, data["revision"], pk)
            elif kind == "appointments":
                saved = save_appointment(request.user, home.pk, data, data["revision"], pk)
            else:
                raise ValidationError("अमान्य निर्देशिका रिकॉर्ड।")
            return redirect(parent_url(kind, saved))
        except EditConflict as exc:
            form.add_error(None, exc)
            status = 409
        except ValidationError as exc:
            for message in exc.messages:
                form.add_error(None, message)
        except IntegrityError:
            form.add_error(
                None, "तिथि, दोहराव या समकालीन बदलाव के कारण सहेजा नहीं गया। वर्तमान रिकॉर्ड जाँचें।"
            )
            status = 409
    back = (
        parent_url(kind, obj)
        if pk
        else (
            reverse(
                "expert_detail",
                args=["experts", home.pk],
            )
            if home
            else reverse("expert_list", args=[kind])
        )
    )
    return render(
        request,
        "experts/form.html",
        {"form": form, "title": title, "back": back, "kind": kind, "is_edit": bool(pk)},
        status=status,
    )


def field_labels():
    labels = {"revision": "संशोधन", "subjects": "विषय", "sequence": "स्थायी क्रमांक"}
    for model, _, _ in REGISTRY.values():
        for field in model._meta.fields:
            labels[field.name] = str(field.verbose_name)
    labels.update(
        {
            "state": "स्थिति",
            "version": "संस्करण",
            "previous_version": "पूर्व संस्करण",
            "expert": "विशेषज्ञ",
        }
    )
    return labels


def audit_rows(data, contacts):
    labels = field_labels()
    output = []
    for key, value in data.items():
        if key in {"mobile", "email"} and not contacts:
            continue
        if key == "candidate_list":
            continue
        if isinstance(value, bool):
            value = "हाँ" if value else "नहीं"
        output.append((labels.get(key, key), value if value is not None else "—"))
    return output


@permitted(*READ)
@require_GET
def detail(request, kind, pk):
    model, form_class, title = spec(kind)
    obj = get_object_or_404(model, pk=pk)
    if kind != "experts":
        return redirect(parent_url(kind, obj))
    contacts = bool(roles_for(request.user) & {Role.MASTER, Role.PROCESSOR})
    fields = form_class(instance=obj).fields
    rows = []
    for name, field in fields.items():
        if name in {"reason", "revision"} or (name in {"mobile", "email"} and not contacts):
            continue
        value = getattr(obj, name)
        if name == "subjects":
            value = ", ".join(str(subject) for subject in obj.subjects.all())
        elif isinstance(value, bool):
            value = "हाँ" if value else "नहीं"
        elif hasattr(obj, f"get_{name}_display"):
            value = getattr(obj, f"get_{name}_display")()
        rows.append((field.label, "—" if value is None or value == "" else value))
    check_form = CheckContextForm(request.GET or None, label_suffix="")
    at_date = college = None
    if check_form.is_bound and check_form.is_valid():
        at_date, college = check_form.cleaned_data["at_date"], check_form.cleaned_data["college"]
    issues = []
    context = {"title": title, "kind": kind, "record": obj, "rows": rows, "check_form": check_form}
    if kind == "experts":
        context["appointments"] = obj.appointments.select_related("institution")
        context["duplicates"] = (
            Expert.objects.filter(name__iexact=obj.name).exclude(pk=obj.pk).exists()
        )
    context.update(issues=issues, events=Paginator([], 15).get_page(1))
    return render(request, "experts/detail.html", context)
