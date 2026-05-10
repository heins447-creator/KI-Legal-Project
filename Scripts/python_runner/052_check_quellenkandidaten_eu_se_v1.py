# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_052_check_quellenkandidaten_eu_se_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

REQUIRED_TABLES = [
    "source_candidate_registry",
    "source_candidate_classification",
    "source_candidate_review_rule",
    "source_candidate_jurisdiction_map",
    "source_candidate_language_map",
]

REQUIRED_CANDIDATES = [
    "eu_eurlex_cellar_eli",
    "eu_ecli",
    "eu_justice_portal",
    "eu_iate",
    "eu_eurovoc",
    "eu_dgt_tm",
    "eu_ccbe",
    "se_law_candidate",
    "se_court_candidate",
    "se_bar_candidate",
]


def log(text: str = "") -> None:
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {text}"
    print(line)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.open("a", encoding="utf-8").write(line + "\n")


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
        if DUCKDB_MODULE:
            self.con = duckdb.connect(str(DB_PATH), read_only=True)
        elif not self.exe:
            raise RuntimeError("Weder Python-Modul duckdb noch duckdb.exe gefunden.")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.con is not None:
            self.con.close()

    def scalar(self, sql: str) -> int:
        if self.con is not None:
            return int(self.con.execute(sql).fetchone()[0])
        result = subprocess.run(
            [self.exe, str(DB_PATH), "-csv", "-noheader", "-c", sql],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return int(result.stdout.strip().splitlines()[0].strip())


def main() -> int:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log("CHECK QUELLENKANDIDATEN EU SE OFFICIAL SOURCES V1 gestartet.")
        log(f"Datenbank: {DB_PATH}")
        log(f"Report: {REPORT}")

        if not DB_PATH.exists():
            raise FileNotFoundError(f"Datenbank fehlt: {DB_PATH}")

        with Db() as db:
            for table in REQUIRED_TABLES:
                count = db.scalar(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    f"WHERE table_name = '{table}';"
                )
                if count != 1:
                    raise RuntimeError(f"Tabelle fehlt: {table}")
                log(f"OK Tabelle: {table}")

            for candidate in REQUIRED_CANDIDATES:
                count = db.scalar(
                    f"SELECT COUNT(*) FROM source_candidate_registry WHERE candidate_code = '{candidate}';"
                )
                if count != 1:
                    raise RuntimeError(f"Kandidat fehlt: {candidate}")
                log(f"OK Kandidat: {candidate}")

            total_candidates = db.scalar("SELECT COUNT(*) FROM source_candidate_registry;")
            if total_candidates > 25:
                raise RuntimeError(f"Massendatenverdacht: source_candidate_registry enthaelt {total_candidates} Eintraege.")
            log(f"OK keine Massendaten: source_candidate_registry={total_candidates}")

        log("OK: Quellenkandidaten EU SE Official Sources V1 pruefbar.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
