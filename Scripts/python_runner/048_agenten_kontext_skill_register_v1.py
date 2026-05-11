# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
MIGRATION = ROOT / "Database" / "Migrations" / "012_agenten_kontext_skill_register_v1.sql"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_048_agenten_kontext_skill_register_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

def log(text: str = "") -> None:
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {text}"
    print(line)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.open("a", encoding="utf-8").write(line + "\n")

try:
    import duckdb  # type: ignore
except Exception as exc:
    print(f"FEHLER: duckdb-Modul fehlt: {exc}")
    sys.exit(1)

def main() -> int:
    try:
        log("AGENTEN KONTEXT SKILL REGISTER V1 gestartet.")
        log(f"Datenbank: {DB_PATH}")
        log(f"Migration: {MIGRATION}")
        log(f"Report: {REPORT}")

        if not MIGRATION.exists():
            raise FileNotFoundError(f"Migration fehlt: {MIGRATION}")

        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        sql = MIGRATION.read_text(encoding="utf-8")

        con = duckdb.connect(str(DB_PATH))
        try:
            con.execute(sql)
        finally:
            con.close()

        log("OK: Migration 012 angewendet.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())