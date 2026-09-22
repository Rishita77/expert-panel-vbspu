from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

from .models import StaffUser


class StaffBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = StaffUser.objects.get(username__iexact=username.strip())
        except StaffUser.DoesNotExist:
            StaffUser().set_password(password)
            return None
        if (
            user.check_password(password)
            and self.user_can_authenticate(user)
            and not (
                user.must_change_password
                and user.temporary_password_expires_at
                and user.temporary_password_expires_at <= timezone.now()
            )
        ):
            return user
