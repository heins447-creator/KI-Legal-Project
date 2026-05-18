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
REPORT = LOG_DIR / f"RUN_047_check_quellenbetreuer_fachanwaltsraster_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

REQUIRED_TABLES = [
    "source_registry",
    "source_adapter_registry",
    "source_health_check",
    "source_cache_policy",
    "source_change_log",
    "de_specialist_area",
    "country_legal_area_mapping",
    "country_court_route",
    "country_legal_profession",
    "language_package_registry",
    "language_package_source_map",
]

REQUIRED_SOURCES = [
    "eu_justice_portal",
    "ccbe",
    "eurlex_cellar_eli",
    "ecli",
    "iate_vjm",
    "dgt_tm",
    "eurovoc",
    "se_law_source",
    "se_court_source",
    "se_bar_source",
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
        log("CHECK QUELLENBETREUER FACHANWALTSRASTER V1 gestartet.")
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

            area_count = db.scalar("SELECT COUNT(*) FROM de_specialist_area WHERE specialist_area_code = 'arbeitsrecht';")
            if area_count != 1:
                raise RuntimeError("Fachgebiet Arbeitsrecht fehlt.")
            log("OK Fachgebiet: Arbeitsrecht")

            mapping_count = db.scalar(
                "SELECT COUNT(*) FROM country_legal_area_mapping "
                "WHERE country_code = 'SE' AND specialist_area_code = 'arbeitsrecht';"
            )
            if mapping_count < 1:
                raise RuntimeError("Länderzuordnung Schweden/Arbeitsrecht fehlt.")
            log("OK Land/Rechtsgebiet: Schweden/Arbeitsrecht")

            package_count = db.scalar("SELECT COUNT(*) FROM language_package_registry WHERE package_code = 'sv_de_arbeitsrecht_se';")
            if package_count != 1:
                raise RuntimeError("Sprachpaket sv_de_arbeitsrecht_se fehlt.")
            log("OK Sprachpaket: sv_de_arbeitsrecht_se")

            for source_code in REQUIRED_SOURCES:
                count = db.scalar(f"SELECT COUNT(*) FROM source_registry WHERE source_code = '{source_code}';")
                if count != 1:
                    raise RuntimeError(f"Quelle fehlt: {source_code}")
                log(f"OK Quelle: {source_code}")

            total_sources = db.scalar("SELECT COUNT(*) FROM source_registry;")
            if total_sources > 25:
                raise RuntimeError(f"Massendatenverdacht: source_registry enthaelt {total_sources} Eintraege.")
            log(f"OK keine Massendaten: source_registry={total_sources}")

        log("OK: Quellenbetreuer Fachanwaltsraster V1 pruefbar.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())