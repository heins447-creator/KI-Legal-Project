#!/usr/bin/env python3
"""Phase 0, AP 0.2: DuckDB-Migrations-Runner.

Der Runner legt die lokale DuckDB-Datenbank an und wendet versionierte
SQL-Migrationen aus Database/Migrations an. Standard ist dry-run; echte
Aenderungen brauchen --execute.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase0_ap02_database_migrations_v1.json"
REPORT_PATH = ROOT / "Reports" / "PHASE0_AP02_MIGRATION_RUNNER_BERICHT.txt"
LOG_PATH = ROOT / "Windows_App" / "Logs" / "PHASE0_AP02_MIGRATION_RUNNER_BERICHT.txt"


@dataclass(frozen=True)
class MigrationFile:
    migration_id: str
    path: Path
    checksum: str
    sql: str


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_migrations(migrations_dir: Path) -> list[MigrationFile]:
    migrations: list[MigrationFile] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        migration_id = path.stem
        sql = path.read_text(encoding="utf-8")
        migrations.append(MigrationFile(migration_id, path, sha256_text(sql), sql))
    if not migrations:
        raise RuntimeError(f"Keine Migrationen gefunden: {migrations_dir}")
    return migrations


def ensure_migration_table(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("CREATE SCHEMA IF NOT EXISTS alin_system")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alin_system.schema_migrations (
            migration_id VARCHAR PRIMARY KEY,
            filename VARCHAR NOT NULL,
            checksum_sha256 VARCHAR NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
            applied_by VARCHAR NOT NULL,
            execution_ms BIGINT NOT NULL,
            status VARCHAR NOT NULL
        )
        """
    )


def load_applied(conn: duckdb.DuckDBPyConnection) -> dict[str, str]:
    ensure_migration_table(conn)
    rows = conn.execute(
        "SELECT migration_id, checksum_sha256 FROM alin_system.schema_migrations WHERE status = 'applied'"
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def load_applied_readonly(db_path: Path) -> dict[str, str]:
    if not db_path.exists():
        return {}
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'alin_system'
              AND table_name = 'schema_migrations'
            """
        ).fetchone()
        if not row or row[0] == 0:
            return {}
        rows = conn.execute(
            "SELECT migration_id, checksum_sha256 FROM alin_system.schema_migrations WHERE status = 'applied'"
        ).fetchall()
        return {item[0]: item[1] for item in rows}
    finally:
        conn.close()


def record_migration(
    conn: duckdb.DuckDBPyConnection,
    migration: MigrationFile,
    execution_ms: int,
) -> None:
    conn.execute(
        """
        INSERT INTO alin_system.schema_migrations (
            migration_id,
            filename,
            checksum_sha256,
            applied_by,
            execution_ms,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            migration.migration_id,
            migration.path.name,
            migration.checksum,
            "phase0_ap02_migration_runner",
            execution_ms,
            "applied",
        ],
    )


def apply_migration(conn: duckdb.DuckDBPyConnection, migration: MigrationFile) -> int:
    start = time.perf_counter()
    conn.execute("BEGIN TRANSACTION")
    try:
        conn.execute(migration.sql)
        execution_ms = int((time.perf_counter() - start) * 1000)
        record_migration(conn, migration, execution_ms)
        conn.execute("COMMIT")
        return execution_ms
    except Exception:
        conn.execute("ROLLBACK")
        raise


def render_report(
    *,
    mode: str,
    db_path: Path,
    migrations: list[MigrationFile],
    pending: list[MigrationFile],
    applied_now: list[tuple[str, int]],
    skipped: list[str],
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.2 MIGRATIONS-RUNNER BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        f"Modus: {mode}",
        f"Datenbank: {db_path}",
        "",
        "ERGEBNIS",
        "-" * 70,
        f"Migrationen gesamt: {len(migrations)}",
        f"Ausstehend vor Lauf: {len(pending)}",
        f"In diesem Lauf angewendet: {len(applied_now)}",
        f"Uebersprungen: {len(skipped)}",
        "",
        "ANGEWENDET",
        "-" * 70,
    ]
    if applied_now:
        for migration_id, execution_ms in applied_now:
            lines.append(f"- {migration_id} ({execution_ms} ms)")
    else:
        lines.append("- keine")
    lines.extend(["", "AUSSTEHEND / DRY-RUN", "-" * 70])
    if mode == "dry-run" and pending:
        for migration in pending:
            lines.append(f"- {migration.migration_id} ({migration.path.name})")
    else:
        lines.append("- keine")
    lines.extend(["", "SPERREN", "-" * 70])
    lines.append("08_Migration wurde nicht beschrieben.")
    lines.append("Keine Internetverbindung, keine Fremd-API, keine echten Mandantendaten.")
    lines.extend(["", "ENDE BERICHT", "=" * 70, ""])
    return "\n".join(lines)


def run(db_path: Path, execute: bool, write_report: bool = True) -> str:
    config = load_config()
    migrations_dir = ROOT / config["database"]["active_migrations_dir"]
    migrations = load_migrations(migrations_dir)
    mode = "execute" if execute else "dry-run"
    if execute:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    applied_now: list[tuple[str, int]] = []
    skipped: list[str] = []
    pending: list[MigrationFile] = []

    if execute:
        conn = duckdb.connect(str(db_path))
        try:
            applied = load_applied(conn)
            for migration in migrations:
                known_checksum = applied.get(migration.migration_id)
                if known_checksum:
                    if known_checksum != migration.checksum:
                        raise RuntimeError(
                            f"Migration geaendert nach Anwendung: {migration.migration_id}"
                        )
                    skipped.append(migration.migration_id)
                    continue
                pending.append(migration)

            for migration in pending:
                execution_ms = apply_migration(conn, migration)
                applied_now.append((migration.migration_id, execution_ms))
        finally:
            conn.close()
    else:
        applied = load_applied_readonly(db_path)
        for migration in migrations:
            known_checksum = applied.get(migration.migration_id)
            if known_checksum:
                if known_checksum != migration.checksum:
                    raise RuntimeError(
                        f"Migration geaendert nach Anwendung: {migration.migration_id}"
                    )
                skipped.append(migration.migration_id)
                continue
            pending.append(migration)

    report = render_report(
        mode=mode,
        db_path=db_path,
        migrations=migrations,
        pending=pending,
        applied_now=applied_now,
        skipped=skipped,
    )
    if write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        LOG_PATH.write_text(report, encoding="utf-8")
    print(report)
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ALIN DuckDB-Migrations-Runner")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Nur anzeigen, keine Migration anwenden.")
    mode.add_argument("--execute", action="store_true", help="Migrationen wirklich anwenden.")
    parser.add_argument("--db-path", help="Optionaler Datenbankpfad fuer Tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = load_config()
    db_path = Path(args.db_path) if args.db_path else ROOT / config["database"]["path"]
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    execute = bool(args.execute)
    run(db_path, execute=execute)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
