# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
MIGRATION = ROOT / "Database" / "Migrations" / "011_quellenbetreuer_fachanwaltsraster_v1.sql"
LOG_DIR = ROOT / "Windows_App" / "Logs"
CACHE_DIR = ROOT / "Data" / "Sources" / "Cache"
REPORT = LOG_DIR / f"RUN_046_quellenbetreuer_fachanwaltsraster_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"


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

        log("QUELLENBETREUER FACHANWALTSRASTER V1 gestartet.")
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
                "migration_id": "011_quellenbetreuer_fachanwaltsraster_v1",
                "note_de": "Quellenbetreuer, Fachanwaltsraster Arbeitsrecht, Schweden, Sprachpaket sv_de_arbeitsrecht_se",
            })

            upsert(db, "de_specialist_area", "specialist_area_code", {
                "specialist_area_code": "arbeitsrecht",
                "name_de": "Fachanwalt fuer Arbeitsrecht",
                "description_de": "Interne deutsche Kanzleirasterung fuer arbeitsrechtliche Mandate.",
                "active": True,
            })

            upsert(db, "country_court_route", "route_code", {
                "route_code": "se_arbeitsrecht_route_v1",
                "country_code": "SE",
                "specialist_area_code": "arbeitsrecht",
                "court_system_name": "Schwedische arbeitsrechtliche Gerichtszustaendigkeit",
                "route_description_de": "Vorbereitetes Raster; genaue Verfahrenszuordnung erfolgt spaeter quellenbezogen.",
                "first_instance": "tingsraett oder arbeitsrechtlich zustaendige Stelle je Fallkonstellation",
                "appeal_instance": "Arbetsdomstolen oder zustaendige Rechtsmittelinstanz je Verfahrensart",
                "highest_instance": "Arbetsdomstolen bzw. oberste zustaendige Instanz je Verfahrensart",
                "status": "vorbereitet",
            })

            upsert(db, "country_legal_area_mapping", "mapping_code", {
                "mapping_code": "de_arbeitsrecht_to_se_arbetsraett_v1",
                "country_code": "SE",
                "country_name_de": "Schweden",
                "specialist_area_code": "arbeitsrecht",
                "foreign_legal_area_name": "arbetsraett",
                "legal_system_note_de": "Deutsches Fachanwaltsgebiet dient nur als interne Kanzleirasterung.",
                "court_route_code": "se_arbeitsrecht_route_v1",
                "status": "vorbereitet",
            })

            upsert(db, "country_legal_profession", "profession_code", {
                "profession_code": "se_advokat_arbetsraett_v1",
                "country_code": "SE",
                "profession_name_native": "advokat / jurist med arbetsraettslig inriktning",
                "profession_name_de": "schwedischer Rechtsanwalt oder Jurist mit arbeitsrechtlicher Ausrichtung",
                "authority_or_bar": "Sveriges advokatsamfund / nationale Berufsquellen",
                "admission_note_de": "Berufs- und Vertretungsbefugnis wird spaeter quellenbezogen gepflegt.",
                "specialist_equivalence_note_de": "Keine unmittelbare Gleichsetzung mit deutschem Fachanwalt.",
                "status": "vorbereitet",
            })

            sources = [
                ("eu_justice_portal", "EU-Justizportal", "eu_justizportal", "EU", None, "multi", 10),
                ("ccbe", "CCBE", "berufsquelle", "EU", None, "multi", 9),
                ("eurlex_cellar_eli", "EUR-Lex / Cellar / ELI", "eu_rechtsquelle", "EU", None, "multi", 8),
                ("ecli", "ECLI", "rechtsprechungskennung", "EU", None, "multi", 7),
                ("iate_vjm", "IATE / VJM", "terminologiequelle", "EU", None, "multi", 6),
                ("dgt_tm", "DGT-TM", "translationsspeicher", "EU", None, "multi", 5),
                ("eurovoc", "EuroVoc", "thesaurus", "EU", None, "multi", 4),
                ("se_law_source", "Nationale Gesetzesquelle Schweden", "nationale_gesetzesquelle", "SE", "SE", "sv", 3),
                ("se_court_source", "Nationale Gerichtsquelle Schweden", "nationale_gerichtsquelle", "SE", "SE", "sv", 2),
                ("se_bar_source", "Nationale Anwaltskammer / Berufsquelle Schweden", "nationale_berufsquelle", "SE", "SE", "sv", 1),
            ]

            for code, name, typ, jurisdiction, country, language, rank in sources:
                native_area = "arbetsraett" if country == "SE" else None
                upsert(db, "source_registry", "source_code", {
                    "source_code": code,
                    "source_name": name,
                    "source_type": typ,
                    "jurisdiction": jurisdiction,
                    "country_code": country,
                    "language_code": language,
                    "specialist_area_code": "arbeitsrecht",
                    "legal_area_native": native_area,
                    "source_rank": rank,
                    "update_status": "vorbereitet",
                    "cache_status": "nicht_geladen",
                    "offline_fallback": "nicht_vorhanden",
                    "url_hint": "",
                    "notes_de": "Startdatensatz fuer Quellenbetreuer V1; noch kein automatischer Abruf.",
                })

                upsert(db, "source_adapter_registry", "adapter_code", {
                    "adapter_code": f"adapter_{code}",
                    "source_code": code,
                    "adapter_type": "manuell_vorgemerkt",
                    "endpoint_hint": "",
                    "auth_required": False,
                    "active": False,
                    "notes_de": "Adapter nur vorgemerkt.",
                })

                upsert(db, "source_cache_policy", "policy_code", {
                    "policy_code": f"cache_{code}",
                    "source_code": code,
                    "cache_scope": "metadaten_und_auszuege",
                    "cache_ttl_seconds": 2592000,
                    "max_cache_size_mb": 100,
                    "offline_fallback_enabled": False,
                    "retention_note_de": "Kein Massendatenimport.",
                })

                upsert(db, "source_health_check", "check_code", {
                    "check_code": f"health_{code}",
                    "source_code": code,
                    "check_status": "nicht_geprueft",
                    "http_status": None,
                    "checked_at": None,
                    "message_de": "Quelle registriert, aber noch nicht technisch geprueft.",
                })

                upsert(db, "source_change_log", "change_code", {
                    "change_code": f"change_{code}_anlage",
                    "source_code": code,
                    "change_type": "anlage",
                    "change_note_de": "Quelle als Startdatensatz angelegt.",
                })

            upsert(db, "language_package_registry", "package_code", {
                "package_code": "sv_de_arbeitsrecht_se",
                "source_language_code": "sv",
                "target_language_code": "de",
                "country_code": "SE",
                "specialist_area_code": "arbeitsrecht",
                "package_name": "Schwedisch-Deutsch Arbeitsrecht Schweden",
                "status": "vorbereitet",
                "context_rules_de": "Rechtsbegriffe duerfen nicht isoliert uebersetzt werden.",
            })

            priority = 100
            for code, *_ in sources:
                upsert(db, "language_package_source_map", "map_code", {
                    "map_code": f"sv_de_arbeitsrecht_se_{code}",
                    "package_code": "sv_de_arbeitsrecht_se",
                    "source_code": code,
                    "source_role": "terminologie_oder_rechtsquelle",
                    "priority": priority,
                })
                priority -= 5

            source_count = int(db.scalar("SELECT COUNT(*) FROM source_registry;"))
            package_count = int(db.scalar("SELECT COUNT(*) FROM language_package_registry WHERE package_code = 'sv_de_arbeitsrecht_se';"))
            area_count = int(db.scalar("SELECT COUNT(*) FROM de_specialist_area WHERE specialist_area_code = 'arbeitsrecht';"))

            log(f"Pruefung source_registry: {source_count}")
            log(f"Pruefung language_package_registry: {package_count}")
            log(f"Pruefung de_specialist_area: {area_count}")

            if source_count < 10:
                raise RuntimeError("Nicht alle Quellen wurden registriert.")
            if package_count != 1:
                raise RuntimeError("Sprachpaket sv_de_arbeitsrecht_se fehlt.")
            if area_count != 1:
                raise RuntimeError("Fachgebiet Arbeitsrecht fehlt.")

        log("OK: Quellenbetreuer Fachanwaltsraster V1 angelegt.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())