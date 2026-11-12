# VBSPU Expert Panel Nomination System

Django application for university staff to process college requests, allocate expert panels, approve final selections, generate Hindi letters, and view reports. The interface supports Hindi and English; official letters remain in Hindi.

## Current workflow

- POC enters and submits requests for colleges.
- Registrar reviews applications. The VC (or Admin) generates panels and approves/locks final selections.
- After VC final lock and letter approval, Registrar/Admin confirms release. POC can view the panel and download its final letter only after that release. Existing approved letters need confirmation too; none are released automatically.
- Proposed names are visible to Registrar, VC and Admin; POC can see the finalised panel.
- Admin maintains accounts and directories. Institutions and experts support validated bulk CSV imports (up to 1,500 rows).
- Associate Professor is a distinct academic designation (CSV: `associate`). It qualifies for additional OBC/SC-ST seats only; a separately held Principal post is evaluated independently.
- VC/Admin can replace a proposed member or draft a change to a locked panel. Replacement options are ranked for the actual seat. A lower-ranked choice requires a recorded reason; a revised proposal needs fresh availability checks. Only confirmation of a locked-panel change reverses and reassigns utilisation.
- Final locking updates utilisation; letters, replacements, reporting and audit records use the saved workflow history.
- Subject Expert proposals contain one Principal from the requesting college, two VC nominees and five Professors, plus required category supplements. Final selection retains both VC nominees and four Professors. Principal/HoD rules are unchanged. See [current composition policy](docs/33-subject-expert-policy-and-allocation-explanations.md).

Earlier workshop documents describe historical phases and may contain superseded decisions. They are not setup instructions.

## Fresh local setup (Windows / PowerShell)

These instructions create a separate local database. They do not copy Railway data or accounts. No existing developer's `.local` directory, SSH keys or credentials are needed.

### 1. Install prerequisites and obtain the project

Install Git, Python **3.13**, and `uv`. Install PostgreSQL **17** with its command-line tools using your normal software installation process. Chrome or Edge is needed for letter PDF generation; Windows must have a Devanagari font such as Mangal or Noto Sans Devanagari.

The repository is private: your GitHub account must have access.

```powershell
git clone https://github.com/Rishita77/expert-panel-vbspu.git
cd expert-panel-vbspu
uv sync --frozen --all-groups
```

Run subsequent commands from this folder. They use `.venv` explicitly, so activation is optional. If you prefer activation, use `.\.venv\Scripts\Activate.ps1`.

### 2. Create an empty local PostgreSQL database

Start the PostgreSQL 17 service installed on your computer. The commands below assume the standard Windows installation path and port 5432; adjust them if your installation differs. Connect as the PostgreSQL administrator you created during installation:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -h 127.0.0.1 -p 5432 -U postgres -d postgres
```

At the `psql` prompt, execute these statements once:

```sql
CREATE ROLE vbspu_app LOGIN;
\password vbspu_app
CREATE DATABASE vbspu_foundation OWNER vbspu_app;
\q
```

The password command prompts privately. Remember that local application password for the next step. Do not reuse production credentials. If these objects already exist, reuse your known local setup rather than recreating or deleting it.

### 3. Configure local settings

Create `.local/foundation.json` in the project folder. This ignored file is required by `config.foundation`:

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use the generated value as `secret_key`, and enter the password from step 2. The file must contain valid JSON (escape any backslashes or double quotes in values):

```json
{
  "secret_key": "PASTE-YOUR-GENERATED-LOCAL-SECRET",
  "database": {
    "NAME": "vbspu_foundation",
    "USER": "vbspu_app",
    "PASSWORD": "YOUR-LOCAL-DATABASE-PASSWORD",
    "HOST": "127.0.0.1",
    "PORT": "5432",
    "OPTIONS": {"connect_timeout": 3}
  }
}
```

Never commit this file. Native local settings do **not** automatically read `.env` or `.env.example`; database settings come from this JSON file. CAPTCHA and email OTP are disabled locally by default. No email provider or CAPTCHA account is required to try the application.

**Existing project-owned database:** if you already have `.local/foundation.json`, keep it. This project's earlier portable PostgreSQL setup uses port **55432**, not 5432. Follow [its start/stop instructions](docs/25-local-development-and-verification.md). Do not run the database-creation steps again.

### 4. Apply migrations and create your first administrator

```powershell
& .\.venv\Scripts\python.exe manage.py migrate --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py setup_staff admin_local --full-name "Local Administrator" --bootstrap --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py check --settings=config.foundation
```

The setup command asks for a password privately. `--bootstrap` works only before any staff account exists. There are no shared/default login credentials. Additional staff accounts and roles can be created through the application's staff administration screen.

### 5. Run the application

```powershell
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.foundation --insecure
```

Open [the local login page](http://127.0.0.1:8000/office/login/) and use the account you just created. Keep the terminal open; `Ctrl+C` stops Django. Python changes reload automatically. Use `Ctrl+F5` after CSS changes.

Always include `--settings=config.foundation` for local application commands. The default `config.settings` is the older model-free preview and does not install the staff/database application. `--insecure` serves local CSS despite `DEBUG=False`; use it only with this loopback development server.

A new database has no institutions, subjects, experts or requests. Start with institutions and subjects, then enter/import experts, then submit a request. Panel generation requires enough eligible experts for every required role; starting the server alone does not populate them.

## PDF generation and language support

PDFs use a locally installed Chrome/Edge/Chromium browser. Common browser paths are detected automatically. For a nonstandard installation, set its executable path in the same terminal **before** starting Django:

```powershell
$env:LETTER_PDF_BROWSER_PATH = 'C:\Path\To\chrome.exe'
# Optional: specify a Devanagari font if installed font fallback is unsuitable.
$env:LETTER_DEVANAGARI_FONT_PATH = 'C:\Windows\Fonts\mangal.ttf'
```

Use paths that exist on your computer. Generated documents are stored under `.local/private-documents`. Linux deployment uses Chromium and Noto fonts through the Dockerfile; it does not depend on these Windows paths.

English translation files (`.po` and compiled `.mo`) are committed, so switching languages does not require a translation API. If you edit translations, install GNU gettext with `msgfmt` available on PATH and rebuild:

```powershell
& .\.venv\Scripts\python.exe manage.py compilemessages -l en --ignore=.venv --ignore=.tools --settings=config.foundation
```

Restart Django after rebuilding translations.

## Daily development and troubleshooting

After pulling changes, keep PostgreSQL running and execute:

```powershell
uv sync --frozen --all-groups
& .\.venv\Scripts\python.exe manage.py migrate --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py check --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.foundation --insecure
```

| Symptom | What to check |
| --- | --- |
| Connection refused / timeout | PostgreSQL is running; JSON host and port match your local database. Do not use Railway's private hostname locally. |
| Browser cannot reach localhost | Django must still be running in its terminal; inspect its error output. |
| Missing styles | Use the startup command above with `--insecure`, then hard-refresh. |
| `auth.User` / missing staff model errors | Include `--settings=config.foundation`, including for `manage.py shell`. |
| Login fails on a fresh database | Create the local administrator; deployed accounts are not copied locally. |
| PDF fails | Check installed browser, Devanagari font and write access to `.local/private-documents`. |
| English translations are stale | Recompile edited catalogs and restart Django. |

See [the detailed local guide](docs/25-local-development-and-verification.md) for code checks and inspecting records. Existing automated database tests require a dedicated local PostgreSQL role with `CREATEDB`; the application itself does not need that privilege. Do not run tests against production.

## Deployment and project documentation

Local `runserver` is not a production server. See [Railway deployment and CAPTCHA](docs/31-railway-deployment-and-captcha.md) for production settings and persistent storage. The checked-in `compose.yaml` is an older preview configuration, **not** a complete local staff-application setup; use the instructions above for the full application.

- [Decision log](docs/06-decision-log.md)
- [Requirements traceability](docs/04-requirements-traceability.md)
- [Permissions and VC workflow](docs/27-permissions-and-vc-workflow-workshop.md)
- [Reports and dashboards](docs/28-reports-and-dashboards-workshop.md)
- [Current panel composition and explanations](docs/33-subject-expert-policy-and-allocation-explanations.md)

The original SRS PDF is not included in the repository. Workshop files retain planning history; read later decisions before relying on earlier proposals. Never commit `.local`, `.env`, private documents, database dumps, or SSH keys.
