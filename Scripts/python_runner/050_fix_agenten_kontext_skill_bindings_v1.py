# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
DB_PATH = ROOT / "Database" / "Legal_Brain.duckdb"
LOG_DIR = ROOT / "Windows_App" / "Logs"
REPORT = LOG_DIR / f"RUN_050_fix_agenten_kontext_skill_bindings_v1_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

TABLES = [
    "agent_role_registry",
    "agent_skill_registry",
    "agent_scope_rule",
    "agent_handoff_protocol",
    "agent_handoff_route",
    "agent_uncertainty_rule",
    "agent_source_binding",
    "agent_language_package_binding",
]

REQUIRED_ROLES = [
    "se_arbeitsrecht_federfuehrend",
    "quellenbetreuer",
    "sprachpaket_sv_de_arbeitsrecht_se",
    "medizinrecht_pruefagent",
    "sozialrecht_pruefagent",
    "zivilrecht_pruefagent",
]

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

def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def table_exists(con, table: str) -> bool:
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()[0] == 1

def table_info(con, table: str):
    return con.execute(f"PRAGMA table_info({q(table)})").fetchall()

def columns(con, table: str) -> list[str]:
    return [r[1] for r in table_info(con, table)]

def first_existing(cols: list[str], candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def pk_column(info) -> str | None:
    for row in info:
        if int(row[5]) > 0:
            return row[1]
    return None

def default_value(col: str, typ: str, fallback: str, seq: int):
    n = col.lower()
    t = (typ or "").upper()

    if "created_at" in n or "updated_at" in n or n.endswith("_at"):
        return dt.datetime.now()

    if "active" in n or "allowed" in n or "enabled" in n or "required" in n:
        return True

    if "bool" in t:
        return False

    if "int" in t:
        return seq

    if n in ("country_code", "country"):
        return "SE"

    if n in ("language_code", "document_language_code"):
        return "sv"

    if "source_language" in n:
        return "sv"

    if "target_language" in n:
        return "de"

    if "specialist_area" in n or "legal_area" in n:
        return "arbeitsrecht"

    if "package" in n:
        return "sv_de_arbeitsrecht_se"

    if "source_code" in n:
        return "se_law_source"

    if "status" in n:
        return "aktiv"

    if "role" in n and "code" in n:
        return fallback

    if "agent" in n and "code" in n:
        return fallback

    if "code" in n:
        return fallback

    if "name" in n:
        return fallback

    if "description" in n or "text" in n or "note" in n or "scope" in n or "field" in n or "purpose" in n:
        return "Startdatensatz fuer Agenten-Kontext- und Skill-Register V1."

    return "vorbereitet"

def ensure_row(con, table: str, key_candidates: list[str], row: dict, fallback: str, seq: int) -> None:
    info = table_info(con, table)
    cols = [r[1] for r in info]
    lower_row = {str(k).lower(): v for k, v in row.items()}

    key_col = first_existing(cols, key_candidates)
    if not key_col:
        key_col = pk_column(info)
    if not key_col:
        key_col = first_existing(cols, ["code", "id"])

    values = {}

    for cid, col, typ, notnull, default, pk in info:
        low = col.lower()

        if low in lower_row:
            values[col] = lower_row[low]
        elif key_col and col == key_col:
            if "int" in (typ or "").upper():
                values[col] = seq
            else:
                values[col] = fallback
        elif int(notnull) == 1 and default is None:
            values[col] = default_value(col, typ, fallback, seq)

    for col in cols:
        low = col.lower()
        if low in lower_row and col not in values:
            values[col] = lower_row[low]

    if not values:
        raise RuntimeError(f"Keine einfügbaren Werte fuer {table}")

    if key_col and key_col in values:
        con.execute(f"DELETE FROM {q(table)} WHERE {q(key_col)} = ?", [values[key_col]])

    insert_cols = list(values.keys())
    placeholders = ", ".join(["?"] * len(insert_cols))
    col_sql = ", ".join(q(c) for c in insert_cols)

    con.execute(
        f"INSERT INTO {q(table)} ({col_sql}) VALUES ({placeholders})",
        [values[c] for c in insert_cols],
    )

def clear_table(con, table: str) -> None:
    if table_exists(con, table):
        con.execute(f"DELETE FROM {q(table)}")

def count_rows(con, table: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0])

def seed(con) -> None:
    for table in reversed(TABLES):
        clear_table(con, table)

    role_rows = [
        ("se_arbeitsrecht_federfuehrend", "Federführender Arbeitsrechtsagent Schweden", "SE", "sv", "arbeitsrecht"),
        ("quellenbetreuer", "Quellenbetreuer-Agent", "EU", "multi", "allgemein"),
        ("sprachpaket_sv_de_arbeitsrecht_se", "Sprachpaket-Agent Schwedisch Deutsch Arbeitsrecht Schweden", "SE", "sv", "arbeitsrecht"),
        ("medizinrecht_pruefagent", "Medizinrecht-Prüfagent nur für strukturierte Übergabe", "DE", "de", "medizinrecht"),
        ("sozialrecht_pruefagent", "Sozialrecht-Prüfagent nur für strukturierte Übergabe", "DE", "de", "sozialrecht"),
        ("zivilrecht_pruefagent", "Zivilrecht-Prüfagent nur für strukturierte Übergabe", "DE", "de", "zivilrecht"),
    ]

    seq = 1

    for code, name, country, language, area in role_rows:
        ensure_row(con, "agent_role_registry", ["role_code", "agent_code", "code"], {
            "role_code": code,
            "agent_code": code,
            "code": code,
            "role_name_de": name,
            "agent_name_de": name,
            "name_de": name,
            "role_description_de": name + ". Keine Entscheidung außerhalb des freigegebenen Fach- und Quellenrahmens.",
            "country_code": country,
            "language_code": language,
            "specialist_area_code": area,
            "source_language_code": "sv",
            "target_language_code": "de",
            "status": "aktiv",
        }, code, seq)
        seq += 1

    skill_rows = [
        ("skill_arbeitsrecht_se_quellenbindung", "se_arbeitsrecht_federfuehrend", "Quellengebundene arbeitsrechtliche Vorstrukturierung Schweden"),
        ("skill_arbeitsrecht_se_handoff", "se_arbeitsrecht_federfuehrend", "Erzeugung strukturierter Übergaben an fremde Rechtsgebiete"),
        ("skill_quellenregister_pflege", "quellenbetreuer", "Pflege und Prüfung freigegebener Quellenregister"),
        ("skill_sprachpaket_sv_de", "sprachpaket_sv_de_arbeitsrecht_se", "Kontextgebundene Terminologie Schwedisch-Deutsch Arbeitsrecht"),
        ("skill_medizinrecht_pruefung", "medizinrecht_pruefagent", "Nur medizinrechtliche Prüfantwort auf Übergabe"),
        ("skill_sozialrecht_pruefung", "sozialrecht_pruefagent", "Nur sozialrechtliche Prüfantwort auf Übergabe"),
        ("skill_zivilrecht_pruefung", "zivilrecht_pruefagent", "Nur zivilrechtliche Prüfantwort auf Übergabe"),
    ]

    for code, role, name in skill_rows:
        ensure_row(con, "agent_skill_registry", ["skill_code", "code"], {
            "skill_code": code,
            "code": code,
            "role_code": role,
            "agent_role_code": role,
            "agent_code": role,
            "skill_name_de": name,
            "skill_description_de": name + ". Nur im freigegebenen Test- und Quellenrahmen.",
            "skill_type": "struktur",
            "status": "aktiv",
        }, code, seq)
        seq += 1

    scope_rows = [
        ("scope_arbeitsrecht_se", "se_arbeitsrecht_federfuehrend", "arbeitsrecht", "Schwedisches Arbeitsrecht im vorbereitenden Agentenrahmen", "Keine Bearbeitung fremder Rechtsgebiete ohne Übergabe"),
        ("scope_no_foreign_area_selfwork", "se_arbeitsrecht_federfuehrend", "arbeitsrecht", "Fachübergreifende Fragen nur über Handoff", "Keine medizinrechtliche, sozialrechtliche oder zivilrechtliche Eigenbearbeitung"),
    ]

    for code, role, area, allowed, forbidden in scope_rows:
        ensure_row(con, "agent_scope_rule", ["rule_code", "scope_rule_code", "code"], {
            "rule_code": code,
            "scope_rule_code": code,
            "code": code,
            "role_code": role,
            "agent_role_code": role,
            "country_code": "SE",
            "specialist_area_code": area,
            "allowed_scope_de": allowed,
            "forbidden_scope_de": forbidden,
            "rule_description_de": allowed,
            "status": "aktiv",
        }, code, seq)
        seq += 1

    ensure_row(con, "agent_handoff_protocol", ["protocol_code", "handoff_code", "code"], {
        "protocol_code": "handoff_standard_v1",
        "handoff_code": "handoff_standard_v1",
        "code": "handoff_standard_v1",
        "protocol_name_de": "Standardübergabe für fachübergreifende Agentenprüfung",
        "name_de": "Standardübergabe",
        "required_fields_de": "Ausgangsfrage; betroffene Rechtsgebiete; Land und Rechtssystem; Dokumentfundstelle; Unsicherheitsgrad; konkrete Prüfbitte; Antwort mit Quelle und Fundstelle; Rückgabe an federführenden Agenten.",
        "protocol_description_de": "Fremde Rechtsgebiete dürfen nicht selbst bearbeitet werden.",
        "status": "aktiv",
    }, "handoff_standard_v1", seq)
    seq += 1

    route_rows = [
        ("route_arbeitsrecht_to_medizinrecht_v1", "medizinrecht_pruefagent", "Medizinrechtliche Frage nur über Übergabe"),
        ("route_arbeitsrecht_to_sozialrecht_v1", "sozialrecht_pruefagent", "Sozialrechtliche Frage nur über Übergabe"),
        ("route_arbeitsrecht_to_zivilrecht_v1", "zivilrecht_pruefagent", "Zivilrechtliche Frage nur über Übergabe"),
    ]

    for code, target, trigger in route_rows:
        ensure_row(con, "agent_handoff_route", ["route_code", "handoff_route_code", "code"], {
            "route_code": code,
            "handoff_route_code": code,
            "code": code,
            "source_role_code": "se_arbeitsrecht_federfuehrend",
            "target_role_code": target,
            "from_role_code": "se_arbeitsrecht_federfuehrend",
            "to_role_code": target,
            "protocol_code": "handoff_standard_v1",
            "trigger_de": trigger,
            "route_description_de": trigger,
            "status": "aktiv",
        }, code, seq)
        seq += 1

    uncertainty_rows = [
        ("uncertainty_fundstelle_pflicht_v1", "se_arbeitsrecht_federfuehrend", "mittel", "Unsicherheit und Fundstelle sind bei jeder Übergabe zu markieren."),
        ("uncertainty_foreign_area_v1", "se_arbeitsrecht_federfuehrend", "hoch", "Bei fremdem Rechtsgebiet ist zwingend eine Übergabe zu erzeugen."),
    ]

    for code, role, level, text in uncertainty_rows:
        ensure_row(con, "agent_uncertainty_rule", ["rule_code", "uncertainty_rule_code", "code"], {
            "rule_code": code,
            "uncertainty_rule_code": code,
            "code": code,
            "role_code": role,
            "agent_role_code": role,
            "uncertainty_level": level,
            "rule_text_de": text,
            "rule_description_de": text,
            "status": "aktiv",
        }, code, seq)
        seq += 1

    source_rows = [
        ("bind_arbeitsrecht_se_law_source", "se_arbeitsrecht_federfuehrend", "se_law_source", "Schwedische Gesetzesquelle für Arbeitsrechtsagent"),
        ("bind_arbeitsrecht_se_court_source", "se_arbeitsrecht_federfuehrend", "se_court_source", "Schwedische Gerichtsquelle für Arbeitsrechtsagent"),
        ("bind_quellenbetreuer_eurlex", "quellenbetreuer", "eurlex_cellar_eli", "EU-Quellenpflege durch Quellenbetreuer"),
        ("bind_sprachpaket_iate", "sprachpaket_sv_de_arbeitsrecht_se", "iate_vjm", "Terminologiequelle für Sprachpaket"),
    ]

    for code, role, source, purpose in source_rows:
        ensure_row(con, "agent_source_binding", ["binding_code", "map_code", "source_binding_code", "code"], {
            "binding_code": code,
            "map_code": code,
            "source_binding_code": code,
            "code": code,
            "role_code": role,
            "agent_role_code": role,
            "agent_code": role,
            "source_code": source,
            "binding_purpose_de": purpose,
            "binding_description_de": purpose,
            "status": "aktiv",
        }, code, seq)
        seq += 1

    ensure_row(con, "agent_language_package_binding", ["binding_code", "map_code", "language_binding_code", "code"], {
        "binding_code": "bind_arbeitsrecht_sv_de_package",
        "map_code": "bind_arbeitsrecht_sv_de_package",
        "language_binding_code": "bind_arbeitsrecht_sv_de_package",
        "code": "bind_arbeitsrecht_sv_de_package",
        "role_code": "se_arbeitsrecht_federfuehrend",
        "agent_role_code": "se_arbeitsrecht_federfuehrend",
        "agent_code": "se_arbeitsrecht_federfuehrend",
        "package_code": "sv_de_arbeitsrecht_se",
        "language_package_code": "sv_de_arbeitsrecht_se",
        "source_language_code": "sv",
        "target_language_code": "de",
        "country_code": "SE",
        "specialist_area_code": "arbeitsrecht",
        "binding_purpose_de": "Arbeitsrechtsagent Schweden verwendet Sprachpaket sv_de_arbeitsrecht_se.",
        "binding_description_de": "Arbeitsrechtsagent Schweden verwendet Sprachpaket sv_de_arbeitsrecht_se.",
        "status": "aktiv",
    }, "bind_arbeitsrecht_sv_de_package", seq)

def main() -> int:
    try:
        log("FIX AGENTEN KONTEXT SKILL BINDINGS V1 gestartet.")
        log(f"Datenbank: {DB_PATH}")
        log(f"Report: {REPORT}")

        if not DB_PATH.exists():
            raise FileNotFoundError(f"Datenbank fehlt: {DB_PATH}")

        con = duckdb.connect(str(DB_PATH))

        try:
            for table in TABLES:
                if not table_exists(con, table):
                    raise RuntimeError(f"Tabelle fehlt: {table}")

            seed(con)

            for table in TABLES:
                log(f"{table}: {count_rows(con, table)}")

        finally:
            con.close()

        log("OK: Agenten-Kontext- und Skill-Register Startdaten repariert.")
        return 0

    except Exception as exc:
        log(f"FEHLER: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())