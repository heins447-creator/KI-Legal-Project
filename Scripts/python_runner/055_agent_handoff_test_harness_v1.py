# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
MIGRATION = ROOT / "Database" / "Migrations" / "015_agent_handoff_test_harness_v1.sql"
LOG_DIR = ROOT / "Windows_App" / "Logs"
CACHE_DIR = ROOT / "Data" / "Sources" / "Cache"
REPORT = LOG_DIR / f"RUN_055_agent_handoff_test_harness_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"


def log(text: str = "") -> None:
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {text}"
    print(line)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.open("a", encoding="utf-8").write(line + "\n")


def sql_quote(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def find_duckdb_exe() -> str | None:
    candidates = [
        ROOT / "Tools" / "DuckDB" / "duckdb.exe",
        ROOT / "Tools" / "duckdb.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("duckdb")


try:
    import duckdb  # type: ignore
    DUCKDB_MODULE = True
except Exception:
    duckdb = None
    DUCKDB_MODULE = False


class Db:
    def __init__(self):
        self.exe = find_duckdb_exe()
        self.con = None

    def __enter__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        if DUCKDB_MODULE:
            self.con = duckdb.connect(str(DB_PATH))
        elif not self.exe:
            raise RuntimeError("Weder Python-Modul duckdb noch duckdb.exe gefunden.")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.con is not None:
            self.con.close()

    def execute(self, sql: str):
        if self.con is not None:
            self.con.execute(sql)
            return
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    def scalar(self, sql: str):
        if self.con is not None:
            return self.con.execute(sql).fetchone()[0]
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-csv", "-noheader", "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip().splitlines()[0].strip()


def upsert(db: Db, table: str, key: str, row: dict) -> None:
    cols = list(row.keys())
    values = ", ".join(sql_quote(row[col]) for col in cols)
    col_sql = ", ".join(cols)
    db.execute(f"DELETE FROM {table} WHERE {key} = {sql_quote(row[key])};")
    db.execute(f"INSERT INTO {table} ({col_sql}) VALUES ({values});")


def main() -> int:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        log("AGENT HANDOFF TEST HARNESS V1 gestartet.")
        log(f"Root: {ROOT}")
        log(f"Datenbank: {DB_PATH}")
        log(f"Migration: {MIGRATION}")
        log(f"Report: {REPORT}")

        if not MIGRATION.exists():
            raise FileNotFoundError(f"Migration fehlt: {MIGRATION}")

        with Db() as db:
            db.execute(MIGRATION.read_text(encoding="utf-8"))
            log("Migration angewendet.")

            upsert(db, "schema_migrations", "migration_id", {
                "migration_id": "015_agent_handoff_test_harness_v1",
                "note_de": "Agent Handoff Test Harness V1",
            })

            # Verify counts
            test_case_count = int(db.scalar("SELECT COUNT(*) FROM agent_handoff_test_case;"))
            message_count = int(db.scalar("SELECT COUNT(*) FROM agent_handoff_test_message;"))
            rule_count = int(db.scalar("SELECT COUNT(*) FROM agent_handoff_validation_rule;"))

            log(f"Testfälle: {test_case_count}")
            log(f"Nachrichten: {message_count}")
            log(f"Validierungsregeln: {rule_count}")

            if test_case_count < 3:
                raise RuntimeError("Nicht alle Testfälle angelegt.")
            if message_count < 6:
                raise RuntimeError("Nicht alle Nachrichten angelegt.")
            if rule_count < 5:
                raise RuntimeError("Nicht alle Validierungsregeln angelegt.")

        log("OK: Agent Handoff Test Harness V1 angelegt.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
