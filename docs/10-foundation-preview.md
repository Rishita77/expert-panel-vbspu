# Foundation implementation — local preview

Implemented 9 September 2026 after the user's instruction to start. This is the first independently usable slice of the revised University-only application, not completion of the original Phase 1 package or the full roadmap.

## Available now

- Django 5.2 LTS, Python 3.13, locked Python dependencies and PostgreSQL connection configuration.
- Responsive University workspace with Hindi labels, original placeholder book mark and locally served Bootstrap/HTMX.
- SRS field-based Hindi request preview and explicit edit roundtrip. Nothing is persisted; all preview fields are optional because mandatory submission rules have not been agreed.
- Independently identifiable, immutable Principal, HoD and subject-expert composition policies, with snapshots. Subject-expert policy is marked provisional per DEC-018.
- Read-only policy screen with interactive type switching and ordinary-link fallback.
- Explicit open-reservation notice. No allocation, reservation, final lock, count update or official document action exists.
- Unit/request checks and a desktop/mobile browser smoke test.

## Start on Windows

The current workspace has Python 3.13 and dependencies in `.venv`. Run from the project root:

```powershell
& .\.venv\Scripts\python.exe manage.py preview 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`. Stop with Ctrl+C. The `preview` command refuses to start if database models are installed; it avoids contacting an unrelated local database. It serves local static files with Django's development handler. It is not a production server.

For a clean machine with uv installed:

```powershell
uv sync --frozen --python 3.13
uv run python manage.py preview 127.0.0.1:8000
```

No migrations are required or authorised for this slice. Django authentication/session/admin models are deliberately not installed so the reviewed custom staff identity model can be created in its first migration later. Do not run migrations against an existing local PostgreSQL database based on this preview.

## Container path

```powershell
docker compose up --build web
```

The web port is bound to host loopback. The optional `database` profile provides PostgreSQL 17 with a persistent volume and no published database port; it is not needed by the preview. Set a local development `POSTGRES_PASSWORD` before explicitly enabling that profile. Compose is preparation for later storage work, not evidence of tested database deployment.

Docker was installed but its engine was unavailable in the implementation session. The native Python 3.13 route was used instead. No SQLite fallback, PostgreSQL schema, existing database modifications, or live deployment were used.

## Checks

Implementation-session results: Django system checks passed; 23 automated tests passed; Ruff passed; desktop/mobile Chrome smoke test passed, with screenshots visually inspected. Docker Compose configuration validation passed. Docker image execution and PostgreSQL integration have **not** been verified because the Docker engine was unavailable and no domain schema is implemented.

```powershell
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\ruff.exe check apps config tests manage.py
```

Browser smoke test, with Node.js and Playwright available locally or through `NODE_PATH`:

```powershell
# Optional: use an installed Chrome rather than Playwright's downloaded Chromium.
$env:PLAYWRIGHT_CHANNEL = 'chrome'
node tests/browser_smoke.cjs
```

`test-results/` contains disposable screenshots and is ignored by version control. The browser check verifies Hindi/mixed-text preview, return-to-edit preservation, HTMX type switching, provisional labels, and mobile overflow. The request tests explicitly prohibit unintended database access via pytest-django's default database blocking.

## Boundaries and next slice

This preview is unauthenticated and must stay on loopback with synthetic data. It is not a staff portal ready for deployment. `APP_MODE` values other than `preview` fail at startup. Backend liveness is reported separately from storage readiness.

Next: review the reduced University-only staff/college/request schema and permissions before persistence, then implement expert records and the approved portions of the allocation engine. Reservation policy Q-14 and other open rules stay unresolved and must not receive hidden defaults. The existence of composition policy data does not approve final-selection size, counting dimensions, calendar handling, or lock authority.
