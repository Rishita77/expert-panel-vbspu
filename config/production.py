"""Deployment settings for the Railway-hosted application.

All values that identify a deployment or grant access to it come from Railway
service variables.  This module deliberately has no local-file fallback.
"""

import os
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403
from .settings import INSTALLED_APPS, MIDDLEWARE, TEMPLATES


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} must be set for production.")
    return value


def database_from_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.path:
        raise ImproperlyConfigured("DATABASE_URL must be a PostgreSQL URL.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }


APP_PUBLIC_URL = required("APP_PUBLIC_URL").rstrip("/")
parsed_public_url = urlparse(APP_PUBLIC_URL)
if parsed_public_url.scheme != "https" or not parsed_public_url.hostname:
    raise ImproperlyConfigured("APP_PUBLIC_URL must be an HTTPS public URL.")

SECRET_KEY = required("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = [parsed_public_url.hostname]
DATABASES = {"default": database_from_url(required("DATABASE_URL"))}
ROOT_URLCONF = "config.foundation_urls"
WSGI_APPLICATION = "config.wsgi.application"
AUTH_USER_MODEL = "accounts.StaffUser"
AUTHENTICATION_BACKENDS = ["apps.accounts.auth.StaffBackend"]
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
MIDDLEWARE = [
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
PRIVATE_DOCUMENT_ROOT = Path(required("PRIVATE_DOCUMENT_ROOT"))
LETTER_PDF_NO_SANDBOX = False
LETTER_DEVANAGARI_FONT_PATH = os.environ.get("LETTER_DEVANAGARI_FONT_PATH", "")
LETTER_PDF_BROWSER_PATH = os.environ.get("LETTER_PDF_BROWSER_PATH", "/usr/bin/chromium")
NOMINATION_FRESH_START_DATE = date(2026, 9, 16)

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_TRUSTED_ORIGINS = [APP_PUBLIC_URL]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

# OTP is deliberately deferred.  Deployment configuration cannot accidentally
# turn it on before the University chooses and provisions a delivery method.
EMAIL_OTP_ENABLED = False
EMAIL_OTP_PROVIDER = "console"
DEFAULT_FROM_EMAIL = ""
GMAIL_OAUTH_CLIENT_ID = ""
GMAIL_OAUTH_CLIENT_SECRET = ""
GMAIL_OAUTH_REFRESH_TOKEN = ""

TURNSTILE_ENABLED = os.environ.get("TURNSTILE_ENABLED", "0") == "1"
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")
if TURNSTILE_ENABLED and (not TURNSTILE_SITE_KEY or not TURNSTILE_SECRET_KEY):
    raise ImproperlyConfigured("Turnstile requires both site and secret keys.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
