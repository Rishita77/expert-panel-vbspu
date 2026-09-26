from django.utils.translation import gettext_lazy
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit.services import record

from .access import require_role
from .forms import CredentialIssueForm, EmailOtpForm, PasswordChangeForm
from .login_security import (
    EmailDeliveryError,
    consume_email_login_challenge,
    issue_email_login_challenge,
    verify_turnstile,
)
from .models import EmailLoginChallenge, LoginAttempt, Role, StaffUser
from .services import change_own_password, issue_temporary_password


def allow_attempt(username, address):
    permitted = True
    with transaction.atomic():
        for kind, value, limit in [("user", username.strip().lower(), 5), ("ip", address, 30)]:
            key = salted_hmac("login-" + kind, value).hexdigest()
            now = timezone.now()
            LoginAttempt.objects.get_or_create(key=key, defaults={"window_started": now})
            attempt = LoginAttempt.objects.select_for_update().get(pk=key)
            if now - attempt.window_started >= timedelta(minutes=15):
                attempt.window_started, attempt.attempts = now, 0
            if attempt.attempts >= limit:
                permitted = False
            else:
                attempt.attempts += 1
                attempt.save()
    return permitted


@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.user.is_authenticated:
        return redirect("office_home")
    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    status = 200
    if request.method == "POST":
        if not allow_attempt(
            request.POST.get("username", "")[:150], request.META.get("REMOTE_ADDR", "")
        ):
            form.add_error(None, gettext_lazy("बहुत अधिक प्रयास। कृपया 15 मिनट बाद पुनः प्रयास करें।"))
            status = 429
        elif not verify_turnstile(
            request.POST.get("cf-turnstile-response", ""), request.META.get("REMOTE_ADDR", "")
        ):
            form.add_error(None, gettext_lazy("सुरक्षा जाँच पूरी नहीं हुई। कृपया पुनः प्रयास करें।"))
        elif form.is_valid():
            user = form.get_user()
            if settings.EMAIL_OTP_ENABLED:
                if not user.email:
                    form.add_error(None, gettext_lazy("इस खाते में आधिकारिक ईमेल दर्ज नहीं है। प्रशासक से संपर्क करें।"))
                else:
                    try:
                        challenge = issue_email_login_challenge(
                            user, request.META.get("REMOTE_ADDR", "")
                        )
                    except EmailDeliveryError:
                        form.add_error(None, gettext_lazy("सत्यापन कोड नहीं भेजा जा सका। कृपया पुनः प्रयास करें।"))
                    else:
                        request.session.cycle_key()
                        request.session["pending_email_login_challenge"] = str(challenge.pk)
                        return redirect("email_otp_verify")
            else:
                _complete_login(request, user)
                return redirect("password_change" if user.must_change_password else "office_home")
        
    return render(
        request,
        "office/login.html",
        {
            "form": form,
            "turnstile_enabled": settings.TURNSTILE_ENABLED,
            "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        },
        status=status,
    )


def _complete_login(request, user):
    login(request, user)
    request.session["staff_security_version"] = user.session_security_version
    record(user, "staff.login", user)
    LoginAttempt.objects.filter(
        key=salted_hmac("login-user", user.username.lower()).hexdigest()
    ).delete()


@require_http_methods(["GET", "POST"])
def email_otp_verify(request):
    challenge_id = request.session.get("pending_email_login_challenge")
    if not challenge_id:
        return redirect("login")
    try:
        challenge = EmailLoginChallenge.objects.select_related("user").get(pk=challenge_id)
    except (EmailLoginChallenge.DoesNotExist, ValueError):
        request.session.pop("pending_email_login_challenge", None)
        return redirect("login")
    form = EmailOtpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = consume_email_login_challenge(challenge.pk, form.cleaned_data["code"])
        if user is None:
            form.add_error(None, gettext_lazy("कोड अमान्य, प्रयुक्त या समाप्त हो चुका है।"))
        else:
            request.session.pop("pending_email_login_challenge", None)
            _complete_login(request, user)
            return redirect("password_change" if user.must_change_password else "office_home")
    return render(
        request, "office/email_otp_verify.html", {"form": form, "email": challenge.user.email}
    )


@require_POST
def email_otp_resend(request):
    challenge_id = request.session.get("pending_email_login_challenge")
    if not challenge_id:
        return redirect("login")
    try:
        previous = EmailLoginChallenge.objects.select_related("user").get(pk=challenge_id)
        challenge = issue_email_login_challenge(
            previous.user, request.META.get("REMOTE_ADDR", ""), replacing=previous
        )
    except (EmailLoginChallenge.DoesNotExist, ValueError):
        request.session.pop("pending_email_login_challenge", None)
        return redirect("login")
    except EmailDeliveryError:
        return render(
            request,
            "office/email_otp_verify.html",
            {"form": EmailOtpForm(), "email": previous.user.email, "resend_error": True},
            status=429,
        )
    request.session["pending_email_login_challenge"] = str(challenge.pk)
    return redirect("email_otp_verify")


@require_POST
def sign_out(request):
    if request.user.is_authenticated:
        with transaction.atomic():
            record(request.user, "staff.logout", request.user)
    logout(request)
    return redirect("login")


@require_http_methods(["GET", "POST"])
def password_change(request):
    if not request.user.is_authenticated:
        return redirect("login")
    form = PasswordChangeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            change_own_password(
                request.user,
                form.cleaned_data["current_password"],
                form.cleaned_data["new_password"],
                request,
            )
        except ValidationError as exc:
            for message in exc.messages:
                form.add_error(None, message)
        else:
            return redirect("office_home")
    return render(
        request,
        "office/password_change.html",
        {"form": form, "required": request.user.must_change_password},
    )


@require_http_methods(["GET", "POST"])
def issue_credentials(request, pk):
    if not request.user.is_authenticated:
        return redirect("login")
    require_role(request.user, Role.ADMIN)
    target = get_object_or_404(StaffUser, pk=pk)
    if target == request.user:
        raise PermissionDenied(gettext_lazy("अपने खाते के प्रमाण-पत्र यहाँ से रीसेट नहीं कर सकते।"))
    form = CredentialIssueForm(request.POST or None, target=target)
    if request.method == "POST" and form.is_valid():
        try:
            issue_temporary_password(
                request.user,
                target.pk,
                form.cleaned_data,
                form.cleaned_data["reason"],
                form.cleaned_data["activate"],
            )
        except (PermissionDenied, ValidationError) as exc:
            if isinstance(exc, ValidationError):
                for message in exc.messages:
                    form.add_error(None, message)
            else:
                raise
        else:
            response = render(
                request,
                "office/credential_handover.html",
                {"target": target, "temporary_password": form.cleaned_data["temporary_password"]},
            )
            response["Cache-Control"] = "no-store, max-age=0"
            response["Pragma"] = "no-cache"
            return response
    return render(request, "office/credential_issue.html", {"form": form, "target": target})
