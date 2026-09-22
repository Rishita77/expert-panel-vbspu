# Persistent University foundation — implementation and handover

12 September 2026. The user approved document 11's first-slice package with “LGTM”. This implements that boundary only. Expert pools, allocation, final selection/lock, uploads, scrutiny, letters and reporting remain later slices.

College schema update (DEC-030): affiliation details were subsequently removed at the user's request. Exclude this field from college collection sheets; existing historical audit entries are retained.

## What works

- Administrator-created named University accounts, case-insensitive username login, local password setup and deactivation.
- Explicit roles for account administration, directory maintenance, shared processing and read-only case review. No automatic business permission from Django staff/superuser flags.
- Institution and subject directories with Unicode names, informational optional codes, active status, protected references and revision-aware changes.
- Hindi request drafts requiring college and appointment type; remaining intake fields can be incomplete. Save, reopen, search, edit and inspect attributable history.
- Optimistic revision checks reject stale edits with HTTP 409 and retain the user's posted text. The current record can be opened separately for comparison.
- Business writes and audit commit together. Previous role grants/revocation reasons are retained. No ordinary delete or audit-edit endpoints.
- Local staff, directory and request pages at `/office/`. Original homepage wording and its model-free preview remain unchanged.

## Run the existing setup

Open `http://127.0.0.1:8000/office/`. Demonstration account details are in the ignored local file `.local/demo-access.md`; `demo.poc` has processing and directory permissions. The separate administrator and reviewer accounts demonstrate access boundaries. These are synthetic records and credentials.

Start the project-owned database if it has stopped:

```powershell
& .\.tools\postgresql17\pgsql\bin\pg_ctl.exe -D .\.local\postgres17-foundation -l .\.local\postgres.log -w start
```

Then start the application:

```powershell
& .\.venv\Scripts\python.exe manage.py office 127.0.0.1:8000 --settings=config.foundation
```

Stop the application with Ctrl+C. Stop only the project database when needed:

```powershell
& .\.tools\postgresql17\pgsql\bin\pg_ctl.exe -D .\.local\postgres17-foundation -m fast -w stop
```

Do not run the old preview server and this server on port 8000 together. Windows allowed both listeners during verification; the verified old project preview was stopped. The persistent server still serves the original preview routes.

## Database and secrets

The application uses an isolated PostgreSQL **17.11** cluster bound to `127.0.0.1:55432`, database `vbspu_foundation`, SCRAM password authentication and a project database owner role. The host's installed PostgreSQL 18 instance was not changed. A migration-generation command initially attempted an unauthenticated connection to the settings default port 5432 and failed; foundation settings now refuse to start without explicit project configuration, preventing that fallback.

Portable binaries were obtained from the PostgreSQL Windows distribution provider: [EDB binary downloads](https://www.enterprisedb.com/download-postgresql-binaries), linked by [PostgreSQL's Windows download page](https://www.postgresql.org/download/windows/). Native PostgreSQL startup required execution outside the restricted sandbox. Docker was unavailable, so no Docker execution success is claimed.

`.local/foundation.json` contains the application secret and database connection. `.local/database-admin.json` contains the local cluster administrator credential. `.local/demo-access.json` supports browser verification; the Markdown note is for local demonstration access. All `.local` content is excluded from version control and Docker build context. No credentials are embedded in source, migrations, audit records or test output. Keep the local notes private.

The initial unsuccessful sandbox attempt left an unused `.local/postgres17` directory. It is not the running cluster and must not be used as a fallback database. The successful cluster is explicitly `postgres17-foundation`.

For a fresh workspace, install the locked dependencies, place PostgreSQL 17 binaries at `.tools/postgresql17/pgsql`, then run:

```powershell
& .\.venv\Scripts\python.exe scripts/setup_local_database.py
& .\.venv\Scripts\python.exe manage.py migrate --settings=config.foundation
```

Initialisation refuses to overwrite an existing project cluster/configuration. If interrupted, inspect its state instead of deleting/reinitialising it blindly. The application database role has CREATEDB for isolated pytest test databases; this local verification privilege is not a production role design.

For a synthetic demonstration on an empty staff table:

```powershell
& .\.venv\Scripts\python.exe manage.py seed_foundation_demo --synthetic --settings=config.foundation
```

This refuses existing staff records. Generated passwords are written only to ignored local access notes; the seed source does not contain passwords. Repeated browser walkthroughs add labelled sample subjects, drafts and inactive accounts; they do not remove or reset existing records.

Alternatively, bootstrap a named account on an empty staff table:

```powershell
& .\.venv\Scripts\python.exe manage.py setup_staff rishi --bootstrap --full-name "Rishi" --settings=config.foundation
```

For subsequent administrator-created accounts, use `setup_staff USERNAME --settings=config.foundation` to set a password and activate locally. Password prompts are hidden and validated. This is a privileged local operator action with an explicit system audit actor, not an application self-service reset or a way for ordinary staff to reactivate themselves. Live activation/reset delivery and MFA remain later readiness work.

## Implementation map

| Area | Records / code |
|---|---|
| Staff and access | `apps/accounts`: custom user, role grant history, access mutex, login attempt limiter, services and local commands |
| Directory | `apps/institutions`: institution/subject identities and metadata |
| Requests | `apps/cases`: draft model, validated forms, transactional saves, revision conflict handling, lists/details |
| Audit | `apps/audit`: protected actor references, before/after facts, reasons and Hindi display labels |
| Runtime | `config/foundation.py`, `config/foundation_urls.py`, `scripts/setup_local_database.py` |
| Interface | `templates/office/`, `static/office.css`; separate from the original homepage |

All account and first-slice mutation services acquire the singleton access mutex before rechecking the actor and permissions. This deliberately serialises the small local foundation's writes so role revocation and last-administrator checks cannot race with protected changes. It is not a claim of production throughput or the final allocation concurrency design. Request revisions additionally prevent lost edits after a user has loaded an old form.

Directory activity and requesting-college flags are not EC eligibility verification. Existing draft references remain readable/editable after an institution is deactivated; inactive identities cannot be newly selected. Role-specific directory audit access is restricted to master-data maintainers; processing/reviewer roles can inspect permitted case history.

## Verified results — 12 September 2026

- PostgreSQL 17.11: all 37 foundation tests passed, including real concurrent database transactions.
- Original model-free preview: all 23 tests passed.
- Chrome/Playwright: desktop and mobile journey passed, including the header-overlap regression check.
- Django system check, migration drift check and Ruff passed. Migrations applied successfully from the initially empty project database and again in isolated test database creation.
- Screenshots visually inspected after the mobile spacing correction. No production deployment or Docker runtime verification claimed.

## Verification and demonstration contract

Run database checks against PostgreSQL, not SQLite:

```powershell
& .\.venv\Scripts\python.exe manage.py check --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.foundation
& .\.venv\Scripts\python.exe -m pytest tests/test_foundation.py --ds=config.foundation -q
& .\.venv\Scripts\python.exe -m pytest tests/test_preview.py -q
& .\.venv\Scripts\ruff.exe check apps config tests scripts/setup_local_database.py
```

`tests/foundation_browser.cjs` uses Playwright/Chrome against the running local app and reads the local synthetic access file. On this machine, the bundled Node dependencies supply Playwright via NODE_PATH, as in the preview instructions. It checks login, directory creation/edit, Hindi save/reopen, zero-count display, history, competing browser edits, mobile overflow/header spacing, reviewer denial, administrator separation, staff creation and logout.

Screenshots are written to `test-results/office-desktop.png`, `office-hindi-history.png` and `office-mobile-form.png`. They were visually inspected. The mobile header was adjusted to fit wrapped account controls without overlapping the page heading.

Stakeholder walkthrough:

1. Sign in as the synthetic POC and inspect the two sample colleges and Hindi subject.
2. Create a request draft with college, appointment type and Hindi remarks; leave unfinished evidence fields blank.
3. Save and reopen. Edit with a reason and inspect before/after history.
4. Open one draft in two tabs; save one, then attempt the older edit and review the conflict response.
5. Sign in as reviewer: read cases/history, with direct editing denied.
6. Sign in as administrator: create an inactive named account; inspect explicit roles. Request access remains denied without a processing/reviewer role.

This foundation is a local demonstration, not an operational university release. The next approved workshop is expert identities, single-current-college affiliation history and EC-approved candidate pools. Common final-lock-only utilisation and unchanged pending-offer ranking remain requirements; no allocation engine or utilisation ledger has been implemented here.
