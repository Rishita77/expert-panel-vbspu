#!/bin/sh
set -eu

# Railway mounts the private-document volume after the image is built.  Set its
# ownership at boot, then run every application process as the unprivileged
# account created in the Dockerfile.
mkdir -p "${PRIVATE_DOCUMENT_ROOT:?PRIVATE_DOCUMENT_ROOT must be set}"
chown -R appuser:appuser "$PRIVATE_DOCUMENT_ROOT" /app/staticfiles

exec su -s /bin/sh appuser -c '
  set -eu
  export DJANGO_SETTINGS_MODULE=config.production
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --access-logfile - --error-logfile -
'
