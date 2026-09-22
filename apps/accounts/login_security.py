import base64
import json
import secrets
from datetime import timedelta
from email.message import EmailMessage
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from apps.audit.services import record

from .models import EmailLoginChallenge, StaffUser


class EmailDeliveryError(Exception):
    pass


def ip_hash(address):
    return salted_hmac("email-otp-ip", address).hexdigest()


def verify_turnstile(token, address):
    if not settings.TURNSTILE_ENABLED:
        return True
    if not token or not settings.TURNSTILE_SECRET_KEY:
        return False
    body = urlencode(
        {"secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": address}
    ).encode()
    request = Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 -- fixed Cloudflare endpoint
            return bool(json.loads(response.read().decode()).get("success"))
    except (URLError, TimeoutError, ValueError, OSError):
        return False


def _send_code(user, code):
    subject = "VBSPU कर्मचारी साइन इन सत्यापन कोड"
    body = (
        "आपका VBSPU कर्मचारी साइन इन सत्यापन कोड है: "
        f"{code}\n\nयह कोड 10 मिनट तक वैध है। इसे किसी के साथ साझा न करें।"
    )
    try:
        if settings.EMAIL_OTP_PROVIDER == "gmail_api":
            _send_with_gmail_api(user.email, subject, body)
        elif settings.EMAIL_OTP_PROVIDER == "console":
            delivered = send_mail(
                subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False
            )
            if delivered != 1:
                raise EmailDeliveryError
        else:
            raise EmailDeliveryError
    except Exception as exc:  # Provider details must not reach the sign-in screen.
        raise EmailDeliveryError from exc


def _send_with_gmail_api(recipient, subject, body):
    from google.auth.exceptions import GoogleAuthError
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    if not all(
        [
            settings.GMAIL_OAUTH_CLIENT_ID,
            settings.GMAIL_OAUTH_CLIENT_SECRET,
            settings.GMAIL_OAUTH_REFRESH_TOKEN,
        ]
    ):
        raise EmailDeliveryError
    credentials = Credentials(
        token=None,
        refresh_token=settings.GMAIL_OAUTH_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GMAIL_OAUTH_CLIENT_ID,
        client_secret=settings.GMAIL_OAUTH_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    try:
        credentials.refresh(GoogleRequest())
        message = EmailMessage()
        message["From"] = settings.DEFAULT_FROM_EMAIL
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        gmail.users().messages().send(
            userId="me",
            body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")},
        ).execute()
    except (GoogleAuthError, HttpError, OSError, ValueError) as exc:
        raise EmailDeliveryError from exc


@transaction.atomic
def issue_email_login_challenge(user, address, *, replacing=None):
    """Create and deliver a one-time challenge, retaining only the OTP hash."""
    user = StaffUser.objects.select_for_update().get(pk=user.pk)
    now = timezone.now()
    sent_in_hour = EmailLoginChallenge.objects.filter(
        user=user, sent_at__gte=now - timedelta(hours=1)
    ).count()
    if sent_in_hour >= 3:
        record(user, "staff.otp_resend_limited", user)
        raise EmailDeliveryError("limit")
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = EmailLoginChallenge.objects.create(
        user=user,
        otp_hash=make_password(code),
        expires_at=now + timedelta(minutes=10),
        request_ip_hash=ip_hash(address),
    )
    try:
        _send_code(user, code)
    except EmailDeliveryError:
        challenge.delete()
        record(user, "staff.otp_delivery_failed", user)
        raise
    if replacing is not None:
        EmailLoginChallenge.objects.filter(
            pk=replacing.pk, consumed_at__isnull=True
        ).update(consumed_at=now)
    challenge.sent_at = now
    challenge.save(update_fields=["sent_at"])
    record(user, "staff.otp_issued", user)
    return challenge


@transaction.atomic
def consume_email_login_challenge(challenge_id, code):
    challenge = EmailLoginChallenge.objects.select_for_update().select_related("user").get(
        pk=challenge_id
    )
    now = timezone.now()
    if (
        challenge.consumed_at is not None
        or challenge.expires_at <= now
        or challenge.attempts >= 5
        or not challenge.user.is_active
    ):
        record(challenge.user, "staff.otp_failed", challenge.user)
        return None
    if not check_password(code, challenge.otp_hash):
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])
        record(challenge.user, "staff.otp_failed", challenge.user)
        return None
    challenge.consumed_at = now
    challenge.save(update_fields=["consumed_at"])
    record(challenge.user, "staff.otp_verified", challenge.user)
    return challenge.user
