from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


class PasswordChangeRequiredMiddleware:
    """Keep temporary-password accounts out of operational pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        allowed = {reverse("login"), reverse("logout"), reverse("password_change")}
        if user.is_authenticated and user.must_change_password and request.path not in allowed:
            if (
                user.temporary_password_expires_at
                and user.temporary_password_expires_at <= timezone.now()
            ):
                logout(request)
                return redirect("login")
            return redirect("password_change")
        return self.get_response(request)


class SessionSecurityMiddleware:
    """Invalidate a target account's existing sessions after a security-sensitive change."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            expected = request.session.get("staff_security_version")
            if expected != user.session_security_version:
                logout(request)
                return redirect("login")
        return self.get_response(request)
