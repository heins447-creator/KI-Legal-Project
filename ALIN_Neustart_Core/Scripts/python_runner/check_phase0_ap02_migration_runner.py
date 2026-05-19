#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.2.

Die Pruefung nutzt eine temporaere DuckDB-Datei unter Windows_App/Logs und
beruehrt die produktive Datenbank nicht.
"""

from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "Scripts" / "python_runner" / "phase0_ap02_migration_runner.py"
CONFIG = ROOT / "Config" / "phase0_ap02_database_migrations_v1.json"
TEMP_DB = ROOT / "Windows_App" / "Logs" / "phase0_ap02_check.duckdb"
PROD_DB = ROOT / "Database" / "DuckDB" / "alin_local.duckdb"
DOC = ROOT / "Projektplanung" / "PHASE0_AP02_MIGRATION_RUNNER.md"
REPORT = ROOT / "Reports" / "PHASE0_AP02_MIGRATION_RUNNER_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP02_MIGRATION_RUNNER_BERICHT.txt"


def fail(message: str) -> None:
    raise AssertionError(message)


def load_runner():
    spec = importlib.util.spec_from_file_location("phase0_ap02_migration_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        fail("Migrations-Runner konnte nicht geladen werden.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def table_exists(conn: duckdb.DuckDBPyConnection, schema: str, table: str) -> bool:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, table],
    ).fetchone()
    return bool(row and row[0] == 1)


def main() -> int:
    runner = load_runner()
    for path in [CONFIG, DOC]:
        if not path.exists():
            fail(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config["database"]["active_migrations_dir"] == "08_Migration":
        fail("Aktive Migrationen duerfen nicht in 08_Migration liegen.")

    if TEMP_DB.exists():
        TEMP_DB.unlink()

    runner.run(TEMP_DB, execute=True, write_report=False)

    if not TEMP_DB.exists():
        fail("Temporaere Testdatenbank wurde nicht angelegt.")

    conn = duckdb.connect(str(TEMP_DB))
    try:
        for schema, table in [
            ("alin_system", "schema_migrations"),
            ("alin_system", "database_metadata"),
            ("alin_audit", "audit_events"),
        ]:
            if not table_exists(conn, schema, table):
                fail(f"Tabelle fehlt: {schema}.{table}")

        migrations = conn.execute(
            "SELECT migration_id FROM alin_system.schema_migrations ORDER BY migration_id"
        ).fetchall()
        migration_ids = [row[0] for row in migrations]
        if migration_ids != ["0001_system_schema", "0002_audit_foundation"]:
            fail(f"Unerwartete Migrationen: {migration_ids}")

        metadata = dict(
            conn.execute("SELECT key, value FROM alin_system.database_metadata").fetchall()
        )
        if metadata.get("internet_policy") != "offline_first_no_foreign_api":
            fail("Internet-Policy fehlt in database_metadata.")
    finally:
        conn.close()

    dry_run_report = runner.run(PROD_DB, execute=False, write_report=False)

    if "Modus: dry-run" not in dry_run_report:
        fail("Dry-run wurde nicht korrekt geprueft.")

    print("PHASE 0, AP 0.2: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
