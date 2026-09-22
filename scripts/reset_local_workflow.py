"""Explicit local-only reset approved by the project owner on 20 September 2026.

Defaults to inventory. --apply backs up PostgreSQL and private letters before
clearing the listed workflow tables. Never resets master IDs or expert sequence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "cases_requestdraft", "audit_auditevent", "nominations_assessment",
    "nominations_allocationrun", "nominations_finalselection", "nominations_finalmember",
    "nominations_finalreviewevent", "nominations_utilisationentry",
    "nominations_trackingbaseline", "nominations_panelchange",
    "nominations_panelchangereviewevent", "nominations_replacementcontribution",
    "nominations_utilisationreversal", "nominations_letter",
    "nominations_letterrevision", "nominations_letterevent",
    "panels_approvalrecord", "panels_candidatelist", "panels_poolversion",
    "panels_poolscope", "panels_poolmembership",
}


def fingerprint(connection, table):
    rows = connection.execute(sql.SQL(
        "SELECT row_to_json(t)::text FROM {} t ORDER BY row_to_json(t)::text"
    ).format(sql.Identifier(table))).fetchall()
    return {"count": len(rows), "sha256": hashlib.sha256(
        json.dumps(rows, ensure_ascii=True).encode()
    ).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--drop-legacy-panels", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / ".local/foundation.json").read_text())["database"]
    if (config["HOST"], str(config["PORT"]), config["NAME"]) != (
        "127.0.0.1", "55432", "vbspu_foundation"
    ):
        raise SystemExit("Refusing any database other than the project local demonstration.")
    with psycopg.connect(host=config["HOST"], port=config["PORT"],
                        dbname=config["NAME"], user=config["USER"],
                        password=config["PASSWORD"]) as connection:
        tables = {r[0] for r in connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )}
        targets = sorted(tables & TARGETS)
        keep = sorted(tables - TARGETS)
        before = {table: fingerprint(connection, table) for table in keep}
        counts = {table: fingerprint(connection, table)["count"] for table in targets}
        print(json.dumps({"clear": counts, "retain": {t: v["count"] for t, v in before.items()}}, indent=2))
        if not args.apply:
            return
        backup = ROOT / ".local/backups" / datetime.now().strftime("workflow-reset-%Y%m%d-%H%M%S")
        backup.mkdir(parents=True, exist_ok=False)
        env = dict(os.environ, PGPASSWORD=config["PASSWORD"])
        binary = ROOT / ".tools/postgresql17/pgsql/bin"
        archive = backup / "before-reset.dump"
        subprocess.run([str(binary / "pg_dump.exe"), "-h", config["HOST"], "-p", str(config["PORT"]),
                        "-U", config["USER"], "-d", config["NAME"], "-Fc", "-f", str(archive)],
                       env=env, check=True, capture_output=True)
        subprocess.run([str(binary / "pg_restore.exe"), "--list", str(archive)],
                       check=True, capture_output=True)
        private = (ROOT / ".local/private-documents").resolve()
        if private.exists():
            shutil.copytree(private, backup / "private-documents")
        # No CASCADE: an unexpected dependent table aborts rather than deleting it.
        connection.execute(sql.SQL("TRUNCATE {} RESTRICT").format(
            sql.SQL(", ").join(sql.Identifier(table) for table in targets)
        ))
        after = {table: fingerprint(connection, table) for table in keep}
        if before != after:
            raise RuntimeError("Retained table changed; reset rolled back.")
        connection.commit()
        # All private documents in this project belong to the reset letter workflow.
        if private.exists():
            expected = ROOT.resolve() / ".local" / "private-documents"
            if private != expected:
                raise RuntimeError("Unexpected document directory; files retained.")
            shutil.rmtree(private)
        if args.drop_legacy_panels:
            # These tables were cleared above and are no longer represented in
            # the application after the EC-directory decision.
            for table in [
                "panels_poolmembership", "panels_poolscope", "panels_poolversion",
                "panels_candidatelist", "panels_approvalrecord",
            ]:
                connection.execute(sql.SQL("DROP TABLE IF EXISTS {} RESTRICT").format(sql.Identifier(table)))
            for function in ["panels_approval_guard", "panels_child_guard", "panels_version_guard"]:
                connection.execute(sql.SQL("DROP FUNCTION IF EXISTS {}()").format(sql.Identifier(function)))
        (backup / "reset-manifest.json").write_text(json.dumps(
            {"cleared": counts, "retained_verified": after}, indent=2), encoding="utf-8")
        print("Reset complete; retained tables verified. Backup:", backup)


if __name__ == "__main__":
    main()
