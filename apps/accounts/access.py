from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Role, RoleAssignment


def roles_for(user):
    if not user.is_authenticated or not user.is_active:
        return set()
    return set(
        RoleAssignment.objects.filter(user=user, revoked_at__isnull=True).values_list(
            "role", flat=True
        )
    )


def require_role(user, *roles):
    held = roles_for(user)
    if Role.ADMIN not in held and not held.intersection(roles):
        raise PermissionDenied("इस कार्य की अनुमति नहीं है।")


def permitted(*roles):
    def decorate(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            require_role(request.user, *roles)
            return view(request, *args, **kwargs)

        return wrapped

    return decorate


def context(request):
    roles = roles_for(request.user)
    return {
        "persistent_mode": True,
        "can_accounts": Role.ADMIN in roles,
        "can_master": Role.MASTER in roles,
        "can_process": Role.PROCESSOR in roles,
        "can_reviewer": Role.REVIEWER in roles,
        "can_vc": Role.VC in roles,
        "can_reports": bool(roles & {Role.REVIEWER, Role.VC, Role.ADMIN}),
        "can_cases": bool(roles.intersection({Role.PROCESSOR, Role.REVIEWER, Role.VC, Role.ADMIN})),
        "can_directory": bool(roles),
        "can_experts": bool(
            roles & {Role.MASTER, Role.PROCESSOR, Role.REVIEWER, Role.VC, Role.ADMIN}
        ),
    }
