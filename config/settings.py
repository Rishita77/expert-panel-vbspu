"""Local preview settings. Domain storage and staff authentication are a later slice.

Intentionally excludes Django auth/session/admin models: the revised staff schema
must be reviewed before its first migration. No SQLite substitute is configured.
"""

import os
import secrets
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
if os.environ.get("APP_MODE", "preview") not in {"preview", "foundation", "production"}:
    raise ImproperlyConfigured(
        "APP_MODE must be preview, foundation, or production."
    )

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(48)
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
INSTALLED_APPS = ["django.contrib.staticfiles", "apps.workspace"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.workspace.middleware.PreviewHeadersMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "apps.workspace.context.shell",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "vbspu"),
        "USER": os.environ.get("POSTGRES_USER", "vbspu"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "OPTIONS": {"connect_timeout": 3},
    }
}
LANGUAGE_CODE = "hi"
LANGUAGES = [
    ("hi", "हिन्दी"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# PDF generation is server-side. Configure a font and browser on the host rather
# than assuming Windows paths; an empty font path lets Chromium use its installed
# Devanagari fallback (for example Noto Sans Devanagari on Linux).
LETTER_DEVANAGARI_FONT_PATH = os.environ.get("LETTER_DEVANAGARI_FONT_PATH", "")
LETTER_PDF_BROWSER_PATH = os.environ.get("LETTER_PDF_BROWSER_PATH", "")
LETTER_PDF_NO_SANDBOX = os.environ.get("LETTER_PDF_NO_SANDBOX", "0") == "1"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
SECURE_CONTENT_TYPE_NOSNIFF = True
# Preserve same-origin form provenance for Django's CSRF verification.
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 128 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 50
