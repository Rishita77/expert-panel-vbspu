"""Approved local persistent demonstration; not production settings."""

import json
import os
from datetime import date

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403
from .settings import BASE_DIR, INSTALLED_APPS, MIDDLEWARE, TEMPLATES

local_config = BASE_DIR / ".local" / "foundation.json"
if local_config.exists():
    local = json.loads(local_config.read_text(encoding="utf-8"))
    SECRET_KEY = local["secret_key"]
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", **local["database"]}}
else:
    raise ImproperlyConfigured(
        "Create the isolated project database with scripts/setup_local_database.py first."
    )

ROOT_URLCONF = "config.foundation_urls"
INSTALLED_APPS = [
    *INSTALLED_APPS,
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "apps.accounts",
    "apps.institutions",
    "apps.audit",
    "apps.cases",
    "apps.experts",
    "apps.nominations",
    "apps.reporting",
]
AUTH_USER_MODEL = "accounts.StaffUser"
AUTHENTICATION_BACKENDS = ["apps.accounts.auth.StaffBackend"]
MIDDLEWARE = [
    MIDDLEWARE[0],
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    *MIDDLEWARE[1:],
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.SessionSecurityMiddleware",
    "apps.accounts.middleware.PasswordChangeRequiredMiddleware",
]
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.contrib.auth.context_processors.auth",
    "apps.accounts.access.context",
]
LOGIN_URL = "/office/login/"
LOGIN_REDIRECT_URL = "/office/"
LOGOUT_REDIRECT_URL = LOGIN_URL
# The local Windows demonstration runs Chrome in an isolated developer process.
# Production deployment should leave the shared default disabled and run the
# browser as an unprivileged service account with its sandbox enabled.
LETTER_PDF_NO_SANDBOX = True
PRIVATE_DOCUMENT_ROOT = BASE_DIR / ".local" / "private-documents"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Local development deliberately does not send email or contact Cloudflare unless
# a developer explicitly supplies non-local environment values. Railway production
# enables both controls only after its Gmail OAuth and Turnstile secrets exist.
EMAIL_OTP_ENABLED = os.environ.get("EMAIL_OTP_ENABLED", "0") == "1"
EMAIL_OTP_PROVIDER = os.environ.get("EMAIL_OTP_PROVIDER", "console")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "emailadmin.vbspu@gmail.com")
GMAIL_OAUTH_CLIENT_ID = os.environ.get("GMAIL_OAUTH_CLIENT_ID", "")
GMAIL_OAUTH_CLIENT_SECRET = os.environ.get("GMAIL_OAUTH_CLIENT_SECRET", "")
GMAIL_OAUTH_REFRESH_TOKEN = os.environ.get("GMAIL_OAUTH_REFRESH_TOKEN", "")
TURNSTILE_ENABLED = os.environ.get("TURNSTILE_ENABLED", "0") == "1"
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")
NOMINATION_FRESH_START_DATE = date(2026, 9, 16)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
