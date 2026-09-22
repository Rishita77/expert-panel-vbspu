# Railway deployment and CAPTCHA

## Scope

This is a temporary deployment for fictional data and dry-run use. It deploys
the existing University application, PostgreSQL, private generated letters, and
Cloudflare Turnstile on the login form. Email OTP is intentionally disabled.

## Railway services

Create one Railway project with:

1. **PostgreSQL** — use Railway's PostgreSQL service. Do not use a local
   database or SQLite.
2. **Web service** — deploy this repository using the included `Dockerfile`.
3. **Persistent volume** attached to the web service at
   `/app/private-documents`. Generated PDFs are private and must not be put in
   the repository or a public static directory.

Railway runs the container command, which applies migrations and collects static
files before starting Gunicorn. The health endpoint is `/health/`.

## Required web-service variables

Set these in Railway's web-service variables. Do not commit any of them.

| Variable | Value |
| --- | --- |
| `APP_MODE` | `production` |
| `APP_PUBLIC_URL` | the exact HTTPS Railway public URL, without a trailing slash |
| `DJANGO_SECRET_KEY` | a new long random secret |
| `DATABASE_URL` | reference Railway PostgreSQL's `DATABASE_URL` variable |
| `PRIVATE_DOCUMENT_ROOT` | `/app/private-documents` |
| `TURNSTILE_ENABLED` | `1` |
| `TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile secret key |

Do **not** set `EMAIL_OTP_ENABLED`, Gmail credentials, or any email-provider
credentials. Production settings force email OTP off during this deployment.

## Turnstile setup

In Cloudflare Turnstile, create a managed widget and permit the Railway public
hostname only. Copy its site key and secret key into the two Railway variables.
The form will refuse login if the widget is absent, invalid, or cannot be
verified. Keep Turnstile disabled locally unless deliberately testing it with a
separate local configuration.

## Deployment verification

After deployment, verify the Railway URL is HTTPS, `/health/` responds, and the
login page contains the Turnstile widget. Then use only fictional data to verify
login, request entry, Registrar review, VC panel generation, final lock, report
viewing, letter creation, PDF download, logout, and that a second browser cannot
download a protected PDF without permission.

Before adding real University data or moving to a paid plan, take and download a
database backup, copy the private-document volume, record the Railway project
owner and recovery contact, and repeat the restore process in a separate
environment.
