"""Create a project-owned PostgreSQL 17 cluster. Never touch the host's database.

Run with the project Python. Download PostgreSQL binaries separately into
.tools/postgresql17/pgsql. Credentials remain in ignored .local files.
"""

import json
import secrets
import subprocess
from pathlib import Path

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
BIN = ROOT / ".tools" / "postgresql17" / "pgsql" / "bin"
DATA = LOCAL / "postgres17-foundation"
CONFIG = LOCAL / "foundation.json"
PORT = 55432


def run(name, *args):
    subprocess.run([str(BIN / (name + ".exe")), *map(str, args)], check=True)


def main():
    if CONFIG.exists() or DATA.exists():
        raise SystemExit("Existing project database/config found; refusing to initialise again.")
    version = subprocess.check_output([str(BIN / "postgres.exe"), "--version"], text=True)
    if " 17." not in version:
        raise SystemExit("PostgreSQL 17 binaries required.")
    LOCAL.mkdir(exist_ok=True)
    admin_password, app_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    (LOCAL / "database-admin.json").write_text(
        json.dumps({"password": admin_password}), encoding="utf-8"
    )
    password_file = LOCAL / "init-password"
    password_file.write_text(admin_password, encoding="utf-8")
    try:
        run(
            "initdb",
            "-D",
            DATA,
            "-U",
            "vbspu_local_admin",
            "--encoding=UTF8",
            "--locale=C",
            "--auth=scram-sha-256",
            "--pwfile",
            password_file,
        )
    finally:
        password_file.unlink(missing_ok=True)
    with (DATA / "postgresql.conf").open("a", encoding="utf-8") as stream:
        stream.write(f"\nlisten_addresses = '127.0.0.1'\nport = {PORT}\n")
    run("pg_ctl", "-D", DATA, "-l", LOCAL / "postgres.log", "-w", "start")
    with psycopg.connect(
        host="127.0.0.1",
        port=PORT,
        dbname="postgres",
        user="vbspu_local_admin",
        password=admin_password,
        autocommit=True,
    ) as connection:
        connection.execute(
            sql.SQL("CREATE ROLE vbspu_app LOGIN CREATEDB PASSWORD {}").format(
                sql.Literal(app_password)
            )
        )
        connection.execute("CREATE DATABASE vbspu_foundation OWNER vbspu_app")
    CONFIG.write_text(
        json.dumps(
            {
                "secret_key": secrets.token_urlsafe(48),
                "database": {
                    "NAME": "vbspu_foundation",
                    "USER": "vbspu_app",
                    "PASSWORD": app_password,
                    "HOST": "127.0.0.1",
                    "PORT": str(PORT),
                    "OPTIONS": {"connect_timeout": 3},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (LOCAL / "database-admin.json").write_text(
        json.dumps({"password": admin_password}), encoding="utf-8"
    )
    print("Project PostgreSQL 17 is ready on loopback port 55432. Credentials were not printed.")


if __name__ == "__main__":
    main()
