# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
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
        log("AGENTEN KONTEXT SKILL REGISTER V1 gestartet.")
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
                "migration_id": "012_agenten_kontext_skill_register_v1",
                "note_de": "Agenten-Kontext- und Skill-Register V1",
            })

            # Rollen
            roles = [
                ("agent_arbeitsrecht_se", "Federführender Arbeitsrechtsagent Schweden",
                 "Bearbeitet arbeitsrechtliche Mandate mit Bezug zu Schweden.",
                 "arbeitsrecht", "SE", "sv"),
                ("agent_quellenbetreuer", "Quellenbetreuer-Agent",
                 "Verwaltet Quellenregister, Adapter, Cache und Aktualität.",
                 None, None, None),
                ("agent_sprachpaket_sv_de", "Sprachpaket-Agent sv_de_arbeitsrecht_se",
                 "Zuständig für Übersetzungen und Terminologie im Sprachpaket sv_de_arbeitsrecht_se.",
                 "arbeitsrecht", "SE", "sv"),
                ("agent_medizinrecht_pruef", "Medizinrecht-Prüfagent",
                 "Prüft medizinrechtliche Fragestellungen (fremdes Rechtsgebiet).",
                 "medizinrecht", None, None),
                ("agent_sozialrecht_pruef", "Sozialrecht-Prüfagent",
                 "Prüft sozialrechtliche Fragestellungen (fremdes Rechtsgebiet).",
                 "sozialrecht", None, None),
                ("agent_zivilrecht_pruef", "Zivilrecht-Prüfagent",
                 "Prüft zivilrechtliche Fragestellungen (fremdes Rechtsgebiet).",
                 "zivilrecht", None, None),
            ]
            for code, name, desc, area, country, lang in roles:
                upsert(db, "agent_role_registry", "role_code", {
                    "role_code": code,
                    "role_name_de": name,
                    "role_description_de": desc,
                    "specialist_area_code": area,
                    "country_code": country,
                    "language_code": lang,
                })

            # Skills
            skills = [
                ("skill_arbeitsrecht_se_vertrag", "agent_arbeitsrecht_se",
                 "Arbeitsvertragsprüfung Schweden",
                 "Prüft schwedische Arbeitsverträge auf Rechtskonformität.", "fachlich"),
                ("skill_arbeitsrecht_se_kuendigung", "agent_arbeitsrecht_se",
                 "Kündigungsprüfung Schweden",
                 "Prüft schwedische Kündigungen auf Rechtskonformität.", "fachlich"),
                ("skill_quellenbetreuer_registrierung", "agent_quellenbetreuer",
                 "Quellenregistrierung",
                 "Registriert neue Quellen im Quellenregister.", "fachlich"),
                ("skill_sprachpaket_sv_de_uebersetzung", "agent_sprachpaket_sv_de",
                 "Übersetzung Schwedisch-Deutsch",
                 "Übersetzt schwedische Rechtstexte ins Deutsche.", "fachlich"),
                ("skill_medizinrecht_pruefung", "agent_medizinrecht_pruef",
                 "Medizinrechtliche Prüfung",
                 "Prüft medizinrechtliche Aspekte.", "fachlich"),
                ("skill_sozialrecht_pruefung", "agent_sozialrecht_pruef",
                 "Sozialrechtliche Prüfung",
                 "Prüft sozialrechtliche Aspekte.", "fachlich"),
                ("skill_zivilrecht_pruefung", "agent_zivilrecht_pruef",
                 "Zivilrechtliche Prüfung",
                 "Prüft zivilrechtliche Aspekte.", "fachlich"),
            ]
            for code, role, name, desc, typ in skills:
                upsert(db, "agent_skill_registry", "skill_code", {
                    "skill_code": code,
                    "role_code": role,
                    "skill_name_de": name,
                    "skill_description_de": desc,
                    "skill_type": typ,
                })

            # Scope-Regeln
            scopes = [
                ("scope_arbeitsrecht_se_zustaendig", "agent_arbeitsrecht_se",
                 "arbeitsrecht", "SE", "sv", "zuständig", 100),
                ("scope_quellenbetreuer_allgemein", "agent_quellenbetreuer",
                 None, None, None, "zuständig", 50),
                ("scope_sprachpaket_sv_de_zustaendig", "agent_sprachpaket_sv_de",
                 "arbeitsrecht", "SE", "sv", "zuständig", 90),
                ("scope_medizinrecht_pruef_fremd", "agent_medizinrecht_pruef",
                 "medizinrecht", None, None, "prüfend", 10),
                ("scope_sozialrecht_pruef_fremd", "agent_sozialrecht_pruef",
                 "sozialrecht", None, None, "prüfend", 10),
                ("scope_zivilrecht_pruef_fremd", "agent_zivilrecht_pruef",
                 "zivilrecht", None, None, "prüfend", 10),
            ]
            for code, role, area, country, lang, stype, prio in scopes:
                upsert(db, "agent_scope_rule", "rule_code", {
                    "rule_code": code,
                    "role_code": role,
                    "specialist_area_code": area,
                    "country_code": country,
                    "language_code": lang,
                    "scope_type": stype,
                    "priority": prio,
                })

            # Handoff-Protokolle
            handoffs = [
                ("handoff_arbeitsrecht_zu_medizinrecht", "agent_arbeitsrecht_se",
                 "agent_medizinrecht_pruef",
                 "Fachübergreifende Frage: Medizinrecht",
                 "Ausgangsfrage, betroffene Rechtsgebiete, Land, Dokumentfundstelle, Unsicherheitsgrad, konkrete Prüfbitte",
                 True),
                ("handoff_arbeitsrecht_zu_sozialrecht", "agent_arbeitsrecht_se",
                 "agent_sozialrecht_pruef",
                 "Fachübergreifende Frage: Sozialrecht",
                 "Ausgangsfrage, betroffene Rechtsgebiete, Land, Dokumentfundstelle, Unsicherheitsgrad, konkrete Prüfbitte",
                 True),
                ("handoff_arbeitsrecht_zu_zivilrecht", "agent_arbeitsrecht_se",
                 "agent_zivilrecht_pruef",
                 "Fachübergreifende Frage: Zivilrecht",
                 "Ausgangsfrage, betroffene Rechtsgebiete, Land, Dokumentfundstelle, Unsicherheitsgrad, konkrete Prüfbitte",
                 True),
            ]
            for code, frm, to, reason, fields, resp in handoffs:
                upsert(db, "agent_handoff_protocol", "protocol_code", {
                    "protocol_code": code,
                    "from_role_code": frm,
                    "to_role_code": to,
                    "handoff_reason": reason,
                    "required_fields": fields,
                    "response_required": resp,
                })

            # Handoff-Routen
            routes = [
                ("route_arbeitsrecht_zu_medizinrecht", "agent_arbeitsrecht_se",
                 "agent_medizinrecht_pruef", "medizinrecht", None, None, 10),
                ("route_arbeitsrecht_zu_sozialrecht", "agent_arbeitsrecht_se",
                 "agent_sozialrecht_pruef", "sozialrecht", None, None, 10),
                ("route_arbeitsrecht_zu_zivilrecht", "agent_arbeitsrecht_se",
                 "agent_zivilrecht_pruef", "zivilrecht", None, None, 10),
            ]
            for code, frm, to, area, country, lang, prio in routes:
                upsert(db, "agent_handoff_route", "route_code", {
                    "route_code": code,
                    "from_role_code": frm,
                    "to_role_code": to,
                    "specialist_area_code": area,
                    "country_code": country,
                    "language_code": lang,
                    "priority": prio,
                })

            # Unsicherheitsregeln
            uncertainties = [
                ("uncert_arbeitsrecht_se_hoch", "agent_arbeitsrecht_se",
                 "hoch", "handoff",
                 "Bei hoher Unsicherheit: Übergabe an Prüfagenten für fremdes Rechtsgebiet."),
                ("uncert_arbeitsrecht_se_mittel", "agent_arbeitsrecht_se",
                 "mittel", "nachfragen",
                 "Bei mittlerer Unsicherheit: Rückfrage beim Quellenbetreuer oder Sprachpaket-Agent."),
                ("uncert_arbeitsrecht_se_niedrig", "agent_arbeitsrecht_se",
                 "niedrig", "eigenständig",
                 "Bei niedriger Unsicherheit: Eigenständige Bearbeitung."),
            ]
            for code, role, level, action, detail in uncertainties:
                upsert(db, "agent_uncertainty_rule", "rule_code", {
                    "rule_code": code,
                    "role_code": role,
                    "uncertainty_level": level,
                    "action": action,
                    "action_detail_de": detail,
                })

            # Quellenbindungen
            source_bindings = [
                ("bind_arbeitsrecht_se_eu_justice", "agent_arbeitsrecht_se",
                 "eu_justice_portal", "primär"),
                ("bind_arbeitsrecht_se_ccbe", "agent_arbeitsrecht_se",
                 "ccbe", "primär"),
                ("bind_arbeitsrecht_se_eurlex", "agent_arbeitsrecht_se",
                 "eurlex_cellar_eli", "primär"),
                ("bind_arbeitsrecht_se_ecli", "agent_arbeitsrecht_se",
                 "ecli", "primär"),
                ("bind_arbeitsrecht_se_iate", "agent_arbeitsrecht_se",
                 "iate_vjm", "sekundär"),
                ("bind_arbeitsrecht_se_dgt", "agent_arbeitsrecht_se",
                 "dgt_tm", "sekundär"),
                ("bind_arbeitsrecht_se_eurovoc", "agent_arbeitsrecht_se",
                 "eurovoc", "sekundär"),
                ("bind_arbeitsrecht_se_law", "agent_arbeitsrecht_se",
                 "se_law_source", "primär"),
                ("bind_arbeitsrecht_se_court", "agent_arbeitsrecht_se",
                 "se_court_source", "primär"),
                ("bind_arbeitsrecht_se_bar", "agent_arbeitsrecht_se",
                 "se_bar_source", "primär"),
                ("bind_quellenbetreuer_allgemein", "agent_quellenbetreuer",
                 "eu_justice_portal", "primär"),
                ("bind_sprachpaket_sv_de_alle", "agent_sprachpaket_sv_de",
                 "eu_justice_portal", "primär"),
            ]
            for code, role, source, btype in source_bindings:
                upsert(db, "agent_source_binding", "binding_code", {
                    "binding_code": code,
                    "role_code": role,
                    "source_code": source,
                    "binding_type": btype,
                })

            # Sprachpaketbindungen
            lang_bindings = [
                ("langbind_arbeitsrecht_se", "agent_arbeitsrecht_se",
                 "sv_de_arbeitsrecht_se", "primär"),
                ("langbind_sprachpaket_sv_de", "agent_sprachpaket_sv_de",
                 "sv_de_arbeitsrecht_se", "primär"),
            ]
            for code, role, pkg, btype in lang_bindings:
                upsert(db, "agent_language_package_binding", "binding_code", {
                    "binding_code": code,
                    "role_code": role,
                    "package_code": pkg,
                    "binding_type": btype,
                })

            # Prüfungen
            role_count = int(db.scalar("SELECT COUNT(*) FROM agent_role_registry;"))
            skill_count = int(db.scalar("SELECT COUNT(*) FROM agent_skill_registry;"))
            scope_count = int(db.scalar("SELECT COUNT(*) FROM agent_scope_rule;"))
            handoff_count = int(db.scalar("SELECT COUNT(*) FROM agent_handoff_protocol;"))
            route_count = int(db.scalar("SELECT COUNT(*) FROM agent_handoff_route;"))
            uncert_count = int(db.scalar("SELECT COUNT(*) FROM agent_uncertainty_rule;"))
            source_bind_count = int(db.scalar("SELECT COUNT(*) FROM agent_source_binding;"))
            lang_bind_count = int(db.scalar("SELECT COUNT(*) FROM agent_language_package_binding;"))

            log(f"Rollen: {role_count}")
            log(f"Skills: {skill_count}")
            log(f"Scope-Regeln: {scope_count}")
            log(f"Handoff-Protokolle: {handoff_count}")
            log(f"Handoff-Routen: {route_count}")
            log(f"Unsicherheitsregeln: {uncert_count}")
            log(f"Quellenbindungen: {source_bind_count}")
            log(f"Sprachpaketbindungen: {lang_bind_count}")

            if role_count < 6:
                raise RuntimeError("Nicht alle Rollen angelegt.")
            if skill_count < 7:
                raise RuntimeError("Nicht alle Skills angelegt.")
            if scope_count < 6:
                raise RuntimeError("Nicht alle Scope-Regeln angelegt.")
            if handoff_count < 3:
                raise RuntimeError("Nicht alle Handoff-Protokolle angelegt.")
            if route_count < 3:
                raise RuntimeError("Nicht alle Handoff-Routen angelegt.")
            if uncert_count < 3:
                raise RuntimeError("Nicht alle Unsicherheitsregeln angelegt.")
            if source_bind_count < 12:
                raise RuntimeError("Nicht alle Quellenbindungen angelegt.")
            if lang_bind_count < 2:
                raise RuntimeError("Nicht alle Sprachpaketbindungen angelegt.")

        log("OK: Agenten Kontext Skill Register V1 angelegt.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
