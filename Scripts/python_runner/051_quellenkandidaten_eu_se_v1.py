# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
MIGRATION = ROOT / "Database" / "Migrations" / "013_quellenkandidaten_eu_se_v1.sql"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_051_quellenkandidaten_eu_se_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"


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
        log("QUELLENKANDIDATEN EU SE OFFICIAL SOURCES V1 gestartet.")
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
                "migration_id": "013_quellenkandidaten_eu_se_v1",
                "note_de": "Quellenkandidatenregister und Klassifikation für EU- und SE-Quellen",
            })

            candidates = [
                ("eu_eurlex_cellar_eli", "EUR-Lex / Cellar / ELI", "eu_rechtsquelle", "EU", None, "multi", "arbeitsrecht", None, 10),
                ("eu_ecli", "ECLI", "rechtsprechungskennung", "EU", None, "multi", "arbeitsrecht", None, 9),
                ("eu_justice_portal", "EU-Justizportal", "eu_justizportal", "EU", None, "multi", "arbeitsrecht", None, 8),
                ("eu_iate", "IATE", "terminologiequelle", "EU", None, "multi", "arbeitsrecht", None, 7),
                ("eu_eurovoc", "EuroVoc", "thesaurus", "EU", None, "multi", "arbeitsrecht", None, 6),
                ("eu_dgt_tm", "DGT Translation Memory", "translationsspeicher", "EU", None, "multi", "arbeitsrecht", None, 5),
                ("eu_ccbe", "CCBE", "berufsquelle", "EU", None, "multi", "arbeitsrecht", None, 4),
                ("se_law_candidate", "Schwedische Gesetzesquelle (Kandidat)", "nationale_gesetzesquelle", "SE", "SE", "sv", "arbeitsrecht", "arbetsraett", 3),
                ("se_court_candidate", "Schwedische Gerichtsquelle (Kandidat)", "nationale_gerichtsquelle", "SE", "SE", "sv", "arbeitsrecht", "arbetsraett", 2),
                ("se_bar_candidate", "Schwedische Berufs-/Kammerquelle (Kandidat)", "nationale_berufsquelle", "SE", "SE", "sv", "arbeitsrecht", "arbetsraett", 1),
            ]

            for code, name, typ, jurisdiction, country, lang, area, native, rank in candidates:
                upsert(db, "source_candidate_registry", "candidate_code", {
                    "candidate_code": code,
                    "source_name": name,
                    "source_type": typ,
                    "jurisdiction": jurisdiction,
                    "country_code": country,
                    "language_code": lang,
                    "specialist_area_code": area,
                    "legal_area_native": native,
                    "candidate_rank": rank,
                    "allowed_usage": "terminologie_oder_rechtsquelle",
                    "offline_strategy": "nicht_vorhanden",
                    "cache_strategy": "metadaten_und_auszuege",
                    "review_status": "vorbereitet",
                    "notes_de": "Kandidat ohne Liveabruf; reine Vorbereitung.",
                })

                upsert(db, "source_candidate_classification", "classification_code", {
                    "classification_code": f"class_{code}",
                    "candidate_code": code,
                    "classification_type": "quellentyp",
                    "classification_value": typ,
                    "classification_note_de": "Klassifikation gemäß Quellenbetreuer.",
                })

                upsert(db, "source_candidate_review_rule", "rule_code", {
                    "rule_code": f"rule_{code}_no_live",
                    "candidate_code": code,
                    "rule_type": "kein_liveabruf",
                    "rule_expression": "TRUE",
                    "rule_note_de": "Noch kein Liveabruf; reine Vorbereitung.",
                    "active": True,
                })

                if jurisdiction:
                    upsert(db, "source_candidate_jurisdiction_map", "map_code", {
                        "map_code": f"jur_{code}_{jurisdiction}",
                        "candidate_code": code,
                        "jurisdiction_code": jurisdiction,
                        "jurisdiction_name_de": jurisdiction,
                    })

                if lang:
                    upsert(db, "source_candidate_language_map", "map_code", {
                        "map_code": f"lang_{code}_{lang}",
                        "candidate_code": code,
                        "language_code": lang,
                        "language_name_de": lang,
                    })

            candidate_count = int(db.scalar("SELECT COUNT(*) FROM source_candidate_registry;"))
            log(f"Pruefung source_candidate_registry: {candidate_count}")

            if candidate_count < 10:
                raise RuntimeError("Nicht alle Kandidaten wurden registriert.")

        log("OK: Quellenkandidaten EU SE Official Sources V1 angelegt.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
