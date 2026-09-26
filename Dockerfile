FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
RUN apt-get update \
    && apt-get install --no-install-recommends -y chromium fonts-noto-core gettext \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.12.12
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN /opt/venv/bin/python manage.py compilemessages -l en --ignore=.venv --ignore=.tools
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/private-documents /app/staticfiles \
    && chown -R appuser:appuser /app/private-documents /app/staticfiles
ENV PATH="/opt/venv/bin:$PATH"
EXPOSE 8000
ENTRYPOINT ["/bin/sh", "/app/scripts/docker-entrypoint.sh"]
