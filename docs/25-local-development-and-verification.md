# Running and verifying the application locally

This guide describes the original portable PostgreSQL environment on this computer. For a fresh installation with standard PostgreSQL, follow the [README](../README.md) first. These portable database paths are not included in a clone. This is not a production deployment guide.

## Before you begin

Open PowerShell in the project folder:

```powershell
cd C:\Users\rishi\RRK_OPENS
```

Use the project Python in `.venv`. Do not install packages globally. The local database credentials and application secret are stored in `.local\foundation.json`; do not copy, commit, email, or share that file.

## Start the local database

First check whether PostgreSQL is already running:

```powershell
& .\.tools\postgresql17\pgsql\bin\pg_ctl.exe status -D .\.local\postgres17-foundation
```

If it is not running, start it:

```powershell
& .\.tools\postgresql17\pgsql\bin\pg_ctl.exe -D .\.local\postgres17-foundation -l .\.local\postgres.log -w start
```

On some Windows installations `pg_ctl start` can fail with a restricted-token
error even though the PostgreSQL cluster itself is healthy. In that case, run
the server directly in a separate PowerShell window and leave that window open:

```powershell
& .\.tools\postgresql17\pgsql\bin\postgres.exe -D .\.local\postgres17-foundation
```

The successful startup ends with `database system is ready to accept
connections`. Then use a second window for Django. This is the project-owned
cluster on port 55432; the Windows PostgreSQL service on port 5432 is not the
database used by this portable setup's `config.foundation` configuration.

To stop it when finished:

```powershell
& .\.tools\postgresql17\pgsql\bin\pg_ctl.exe -D .\.local\postgres17-foundation -w stop
```

Never edit files inside `.local\postgres17-foundation`. PostgreSQL manages those files itself.

## Start the web application

Apply any database migrations first:

```powershell
& .\.venv\Scripts\python.exe manage.py migrate --settings=config.foundation
```

Then start the development server:

```powershell
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=config.foundation --insecure
```

Open [http://127.0.0.1:8000/office/](http://127.0.0.1:8000/office/). Leave the PowerShell window open while using the app. Press `Ctrl+C` in that window to stop the server.

This command automatically reloads Python and template changes. If a CSS, image, or other static-file change does not appear, refresh the browser with `Ctrl+F5`.

## Alternative: portable PostgreSQL setup on a new Windows machine

Prefer the standard PostgreSQL installation described in the [README](../README.md). The following helper is Windows-specific and expects separately downloaded binaries. If it fails after creating the cluster (for example with the restricted-token error), do not rerun it or delete the data directory blindly: it does not resume partial initialisation. Starting PostgreSQL alone will not finish role/database/config creation.

1. Install Python 3.13 and the `uv` package manager.
2. From the project folder, create the virtual environment and install the pinned dependencies:

   ```powershell
   uv sync --all-groups
   ```

3. Obtain the approved PostgreSQL 17 Windows binaries and place them under `.tools\postgresql17\pgsql\bin`.
4. Create the isolated project database once:

   ```powershell
   & .\.venv\Scripts\python.exe scripts\setup_local_database.py
   ```

   This command deliberately stops if an existing local database or configuration is present.

5. Apply migrations and create the first administrator account:

   ```powershell
   & .\.venv\Scripts\python.exe manage.py migrate --settings=config.foundation
   & .\.venv\Scripts\python.exe manage.py setup_staff your-login-name --full-name "Your Name" --bootstrap --settings=config.foundation
   ```

   The password is requested privately by the command and is never printed. Use `--bootstrap` only for the first administrator.

## Verify a code change

Run these after changing application code:

```powershell
& .\.venv\Scripts\python.exe manage.py check --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.foundation
& .\.venv\Scripts\python.exe -m ruff check apps tests
```

Run the automated checks against the local PostgreSQL configuration:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.foundation"
& .\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:DJANGO_SETTINGS_MODULE
```

For a smaller, quicker check, replace `pytest -q` with a specific file, such as:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.foundation"
& .\.venv\Scripts\python.exe -m pytest tests\test_experts.py -q
Remove-Item Env:DJANGO_SETTINGS_MODULE
```

If you changed a Django model, create and review a migration before applying it:

```powershell
& .\.venv\Scripts\python.exe manage.py makemigrations --settings=config.foundation
& .\.venv\Scripts\python.exe manage.py migrate --settings=config.foundation
```

Do not edit an existing migration that has already been applied. Create a new migration for each schema change.

## Verify a change through the browser

Use this short routine:

1. Start the database and web application.
2. Sign in with an authorised local staff account.
3. Make one small test record or use a clearly labelled synthetic record.
4. Confirm the screen result and its change-history entry.
5. Run the relevant automated test file and the checks above.

For an institution-field change, open **संस्थाएँ**, add a test institution, then edit it. A new record should not show **परिवर्तन का कारण**; an existing record should require it. For an expert change, open **विशेषज्ञ**, add a test expert, and confirm that the current institution and designation appear in **संस्था और पद का इतिहास** after saving.

## Inspect data safely

Use the application interface for normal data entry. If a development-only inspection is needed, start Django's project-aware shell:

```powershell
& .\.venv\Scripts\python.exe manage.py shell --settings=config.foundation
```

Examples to inspect, without changing anything:

```python
from apps.institutions.models import Institution
Institution.objects.values("name", "is_affiliated_to_vbspu")

from apps.experts.models import Expert
Expert.objects.values("sequence", "name", "is_active")
```

Avoid deleting or directly altering records in the shell. The application records audit events, preserves appointment history, and protects final utilisation records; direct database edits bypass those safeguards.

## Useful diagnostics

Check pending migrations:

```powershell
& .\.venv\Scripts\python.exe manage.py showmigrations --settings=config.foundation
```

If the browser says the site cannot be reached, first start the database, then rerun the web-server command. If the server reports a database connection error, run the PostgreSQL status command above. Application output appears in the PowerShell window that started the server; database output is in `.local\postgres.log`.

## Synthetic demonstration data

Only seed an empty local database with deliberate synthetic data:

```powershell
& .\.venv\Scripts\python.exe manage.py seed_foundation_demo --synthetic --settings=config.foundation
```

Do not use this command once real data exists. A controlled demonstration-data cleanup tool is planned separately; until then, remove test records only through an approved, reviewed process.
