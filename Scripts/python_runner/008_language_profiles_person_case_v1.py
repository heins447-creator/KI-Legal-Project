# -*- coding: utf-8 -*-
import sys
import json
import uuid
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import duckdb

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"
CONFIG = ROOT / "Config" / "language_profiles_person_case_v1.json"

NOW = datetime.datetime.now

EU24 = [
    ("bg", "Bulgarisch", "български", "Bulgarian"),
    ("hr", "Kroatisch", "hrvatski", "Croatian"),
    ("cs", "Tschechisch", "čeština", "Czech"),
    ("da", "Dänisch", "dansk", "Danish"),
    ("nl", "Niederländisch", "Nederlands", "Dutch"),
    ("en", "Englisch", "English", "English"),
    ("et", "Estnisch", "eesti", "Estonian"),
    ("fi", "Finnisch", "suomi", "Finnish"),
    ("fr", "Französisch", "français", "French"),
    ("de", "Deutsch", "Deutsch", "German"),
    ("el", "Griechisch", "ελληνικά", "Greek"),
    ("hu", "Ungarisch", "magyar", "Hungarian"),
    ("ga", "Irisch", "Gaeilge", "Irish"),
    ("it", "Italienisch", "italiano", "Italian"),
    ("lv", "Lettisch", "latviešu", "Latvian"),
    ("lt", "Litauisch", "lietuvių", "Lithuanian"),
    ("mt", "Maltesisch", "Malti", "Maltese"),
    ("pl", "Polnisch", "polski", "Polish"),
    ("pt", "Portugiesisch", "português", "Portuguese"),
    ("ro", "Rumänisch", "română", "Romanian"),
    ("sk", "Slowakisch", "slovenčina", "Slovak"),
    ("sl", "Slowenisch", "slovenščina", "Slovenian"),
    ("es", "Spanisch", "español", "Spanish"),
    ("sv", "Schwedisch", "svenska", "Swedish")
]

CONFIG_DATA = {
    "version": "V1",
    "principle": "Sprache wird getrennt nach Software, Person, Fall, Beteiligtem und Kommunikation geführt.",
    "available_languages": [x[0] for x in EU24],
    "staff_defaults": [
        {
            "staff_key": "LAWYER_DEFAULT",
            "role_key": "anwalt",
            "display_name": "Anwalt",
            "internal_work_language_code": "de",
            "accepted_matter_languages": ["de", "en", "sv"],
            "communication_languages": ["de", "en", "sv"],
            "document_review_languages": ["de", "en", "sv"],
            "default_translation_target_language_code": "de",
            "active": True,
            "notes": "Der Anwalt arbeitet intern deutsch. Auftragssprachen und Kommunikationssprachen sind auswählbar."
        },
        {
            "staff_key": "SECRETARY_DEFAULT",
            "role_key": "sekretariat",
            "display_name": "Sekretariat",
            "internal_work_language_code": "de",
            "accepted_matter_languages": ["de", "en", "sv"],
            "communication_languages": ["de", "en"],
            "document_review_languages": ["de", "en"],
            "default_translation_target_language_code": "de",
            "active": True,
            "notes": "Das Sekretariat arbeitet im Posteingang und Vorzimmer mit eigener Sprachauswahl."
        }
    ],
    "case_templates": [
        {
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "case_label": "Schweden Arbeitsrecht",
            "jurisdiction_country_code": "SE",
            "country_language_code": "sv",
            "procedural_language_code": "sv",
            "internal_work_language_code": "de",
            "source_document_language_code": "sv",
            "target_document_language_code": "de",
            "client_default_language_code": "de",
            "opponent_lawyer_default_language_code": "en",
            "opponent_party_default_language_code": "sv",
            "court_default_language_code": "sv",
            "translation_required": True,
            "interpreter_required": False,
            "notes": "Schwedischer Arbeitsrechtsfall. Landessprache und Prozeßsprache Schwedisch. Interne Arbeitssprache Deutsch. Kommunikation mit gegnerischem Anwalt kann Englisch sein."
        }
    ],
    "participant_templates": [
        {
            "participant_profile_key": "TEMPLATE_SE_ARBEITSRECHT_MANDANT",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "mandant",
            "participant_label": "Mandant",
            "mandate_accepted": False,
            "actual_language_code": "de",
            "communication_language_code": "de",
            "document_language_code": "de",
            "procedural_language_code": "sv",
            "outgoing_language_code": "de",
            "incoming_translation_target_language_code": "de",
            "outgoing_translation_source_language_code": "de",
            "translation_required": True,
            "notes": "Mandantensprache wird erst mandantenbezogen festgelegt, wenn der Auftrag angenommen wird. Vorlagewert deutsch."
        },
        {
            "participant_profile_key": "TEMPLATE_SE_ARBEITSRECHT_GERICHT",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gericht",
            "participant_label": "Schwedisches Gericht",
            "mandate_accepted": True,
            "actual_language_code": "sv",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "procedural_language_code": "sv",
            "outgoing_language_code": "sv",
            "incoming_translation_target_language_code": "de",
            "outgoing_translation_source_language_code": "de",
            "translation_required": True,
            "notes": "Gerichtskommunikation in der Prozeßsprache Schwedisch."
        },
        {
            "participant_profile_key": "TEMPLATE_SE_ARBEITSRECHT_GEGNER_ANWALT",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gegnerischer_anwalt",
            "participant_label": "Gegnerischer Anwalt",
            "mandate_accepted": True,
            "actual_language_code": "sv",
            "communication_language_code": "en",
            "document_language_code": "sv",
            "procedural_language_code": "sv",
            "outgoing_language_code": "en",
            "incoming_translation_target_language_code": "de",
            "outgoing_translation_source_language_code": "de",
            "translation_required": True,
            "notes": "Kommunikation kann Englisch sein. Maßgebliche Verfahrens- und Dokumentensprache bleibt Schwedisch."
        },
        {
            "participant_profile_key": "TEMPLATE_SE_ARBEITSRECHT_GEGENSEITE",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gegenseite",
            "participant_label": "Gegenseite",
            "mandate_accepted": True,
            "actual_language_code": "sv",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "procedural_language_code": "sv",
            "outgoing_language_code": "sv",
            "incoming_translation_target_language_code": "de",
            "outgoing_translation_source_language_code": "de",
            "translation_required": True,
            "notes": "Gegenseite im schwedischen Verfahren."
        }
    ],
    "communication_rules": [
        {
            "rule_key": "SE_ARBEITSRECHT_KOMM_GERICHT",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gericht",
            "default_language_code": "sv",
            "fallback_language_code": "sv",
            "procedural_language_code": "sv",
            "document_language_code": "sv",
            "translation_required": True,
            "notes": "An das Gericht wird in der Prozeßsprache Schwedisch geschrieben."
        },
        {
            "rule_key": "SE_ARBEITSRECHT_KOMM_MANDANT",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "mandant",
            "default_language_code": "de",
            "fallback_language_code": "en",
            "procedural_language_code": "sv",
            "document_language_code": "de",
            "translation_required": True,
            "notes": "Mandantensprache wird nach Annahme konkret festgelegt."
        },
        {
            "rule_key": "SE_ARBEITSRECHT_KOMM_GEGNER_ANWALT",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gegnerischer_anwalt",
            "default_language_code": "en",
            "fallback_language_code": "sv",
            "procedural_language_code": "sv",
            "document_language_code": "sv",
            "translation_required": True,
            "notes": "Kommunikationssprache Englisch möglich; prozessuale Sprache Schwedisch."
        },
        {
            "rule_key": "SE_ARBEITSRECHT_KOMM_INTERN",
            "case_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "intern",
            "default_language_code": "de",
            "fallback_language_code": "en",
            "procedural_language_code": "sv",
            "document_language_code": "de",
            "translation_required": False,
            "notes": "Interne Bearbeitung deutsch."
        }
    ]
}

DDL = {
    "app_languages": """
        CREATE TABLE IF NOT EXISTS app_languages (
            language_code VARCHAR PRIMARY KEY,
            german_name VARCHAR NOT NULL,
            language_name_de VARCHAR,
            language_name_native VARCHAR,
            language_name_en VARCHAR,
            eu_official BOOLEAN,
            active_in_system BOOLEAN,
            default_enabled BOOLEAN,
            notes VARCHAR,
            updated_at TIMESTAMP
        )
    """,
    "staff_language_profiles": """
        CREATE TABLE IF NOT EXISTS staff_language_profiles (
            staff_key VARCHAR PRIMARY KEY,
            role_key VARCHAR,
            display_name VARCHAR,
            internal_work_language_code VARCHAR,
            accepted_matter_languages_json VARCHAR,
            communication_languages_json VARCHAR,
            document_review_languages_json VARCHAR,
            default_translation_target_language_code VARCHAR,
            active BOOLEAN,
            notes VARCHAR,
            updated_at TIMESTAMP
        )
    """,
    "case_language_profiles": """
        CREATE TABLE IF NOT EXISTS case_language_profiles (
            case_key VARCHAR PRIMARY KEY,
            case_label VARCHAR,
            jurisdiction_country_code VARCHAR,
            country_language_code VARCHAR,
            procedural_language_code VARCHAR,
            internal_work_language_code VARCHAR,
            source_document_language_code VARCHAR,
            target_document_language_code VARCHAR,
            client_default_language_code VARCHAR,
            opponent_lawyer_default_language_code VARCHAR,
            opponent_party_default_language_code VARCHAR,
            court_default_language_code VARCHAR,
            translation_required BOOLEAN,
            interpreter_required BOOLEAN,
            notes VARCHAR,
            updated_at TIMESTAMP
        )
    """,
    "case_participant_language_profiles": """
        CREATE TABLE IF NOT EXISTS case_participant_language_profiles (
            participant_profile_key VARCHAR PRIMARY KEY,
            case_key VARCHAR,
            participant_role VARCHAR,
            participant_label VARCHAR,
            mandate_accepted BOOLEAN,
            actual_language_code VARCHAR,
            communication_language_code VARCHAR,
            document_language_code VARCHAR,
            procedural_language_code VARCHAR,
            outgoing_language_code VARCHAR,
            incoming_translation_target_language_code VARCHAR,
            outgoing_translation_source_language_code VARCHAR,
            translation_required BOOLEAN,
            notes VARCHAR,
            updated_at TIMESTAMP
        )
    """,
    "communication_language_rules": """
        CREATE TABLE IF NOT EXISTS communication_language_rules (
            rule_key VARCHAR PRIMARY KEY,
            case_key VARCHAR,
            participant_role VARCHAR,
            default_language_code VARCHAR,
            fallback_language_code VARCHAR,
            procedural_language_code VARCHAR,
            document_language_code VARCHAR,
            translation_required BOOLEAN,
            notes VARCHAR,
            updated_at TIMESTAMP
        )
    """,
    "language_profile_audit": """
        CREATE TABLE IF NOT EXISTS language_profile_audit (
            audit_id VARCHAR PRIMARY KEY,
            audit_time TIMESTAMP,
            audit_area VARCHAR,
            audit_status VARCHAR,
            details VARCHAR
        )
    """
}

REQUIRED = {
    "app_languages": [
        ("language_code", "VARCHAR"),
        ("german_name", "VARCHAR"),
        ("language_name_de", "VARCHAR"),
        ("language_name_native", "VARCHAR"),
        ("language_name_en", "VARCHAR"),
        ("eu_official", "BOOLEAN"),
        ("active_in_system", "BOOLEAN"),
        ("default_enabled", "BOOLEAN"),
        ("notes", "VARCHAR"),
        ("updated_at", "TIMESTAMP")
    ],
    "staff_language_profiles": [
        ("staff_key", "VARCHAR"),
        ("role_key", "VARCHAR"),
        ("display_name", "VARCHAR"),
        ("internal_work_language_code", "VARCHAR"),
        ("accepted_matter_languages_json", "VARCHAR"),
        ("communication_languages_json", "VARCHAR"),
        ("document_review_languages_json", "VARCHAR"),
        ("default_translation_target_language_code", "VARCHAR"),
        ("active", "BOOLEAN"),
        ("notes", "VARCHAR"),
        ("updated_at", "TIMESTAMP")
    ],
    "case_language_profiles": [
        ("case_key", "VARCHAR"),
        ("case_label", "VARCHAR"),
        ("jurisdiction_country_code", "VARCHAR"),
        ("country_language_code", "VARCHAR"),
        ("procedural_language_code", "VARCHAR"),
        ("internal_work_language_code", "VARCHAR"),
        ("source_document_language_code", "VARCHAR"),
        ("target_document_language_code", "VARCHAR"),
        ("client_default_language_code", "VARCHAR"),
        ("opponent_lawyer_default_language_code", "VARCHAR"),
        ("opponent_party_default_language_code", "VARCHAR"),
        ("court_default_language_code", "VARCHAR"),
        ("translation_required", "BOOLEAN"),
        ("interpreter_required", "BOOLEAN"),
        ("notes", "VARCHAR"),
        ("updated_at", "TIMESTAMP")
    ],
    "case_participant_language_profiles": [
        ("participant_profile_key", "VARCHAR"),
        ("case_key", "VARCHAR"),
        ("participant_role", "VARCHAR"),
        ("participant_label", "VARCHAR"),
        ("mandate_accepted", "BOOLEAN"),
        ("actual_language_code", "VARCHAR"),
        ("communication_language_code", "VARCHAR"),
        ("document_language_code", "VARCHAR"),
        ("procedural_language_code", "VARCHAR"),
        ("outgoing_language_code", "VARCHAR"),
        ("incoming_translation_target_language_code", "VARCHAR"),
        ("outgoing_translation_source_language_code", "VARCHAR"),
        ("translation_required", "BOOLEAN"),
        ("notes", "VARCHAR"),
        ("updated_at", "TIMESTAMP")
    ],
    "communication_language_rules": [
        ("rule_key", "VARCHAR"),
        ("case_key", "VARCHAR"),
        ("participant_role", "VARCHAR"),
        ("default_language_code", "VARCHAR"),
        ("fallback_language_code", "VARCHAR"),
        ("procedural_language_code", "VARCHAR"),
        ("document_language_code", "VARCHAR"),
        ("translation_required", "BOOLEAN"),
        ("notes", "VARCHAR"),
        ("updated_at", "TIMESTAMP")
    ],
    "language_profile_audit": [
        ("audit_id", "VARCHAR"),
        ("audit_time", "TIMESTAMP"),
        ("audit_area", "VARCHAR"),
        ("audit_status", "VARCHAR"),
        ("details", "VARCHAR")
    ]
}

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def table_exists(con, table):
    row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        """,
        [table]
    ).fetchone()
    return bool(row and row[0] > 0)

def table_info(con, table):
    rows = con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()
    result = []
    for r in rows:
        result.append({
            "cid": r[0],
            "name": str(r[1]),
            "type": str(r[2] or ""),
            "notnull": bool(r[3]),
            "default": r[4],
            "pk": r[5]
        })
    return result

def ensure_schema(con):
    for table, ddl in DDL.items():
        if not table_exists(con, table):
            con.execute(ddl)
        have = {c["name"].lower() for c in table_info(con, table)}
        for col, dtype in REQUIRED[table]:
            if col.lower() not in have:
                con.execute("ALTER TABLE " + q(table) + " ADD COLUMN " + q(col) + " " + dtype)

def default_value_for_column(col, dtype):
    c = col.lower()
    t = dtype.upper()

    if "time" in c or "date" in c or "TIMESTAMP" in t or "DATE" in t:
        return NOW()

    if "bool" in t or c.startswith("is_") or c in {
        "active", "enabled", "selectable", "eu_official", "active_in_system",
        "default_enabled", "translation_required", "interpreter_required",
        "mandate_accepted"
    }:
        return False

    if "int" in t or "bigint" in t:
        return 0

    return ""

def row_value(row, col, meta):
    if col in row:
        return row[col]

    low = col.lower()

    aliases = {
        "code": "language_code",
        "iso_code": "language_code",
        "iso6391": "language_code",
        "iso_639_1": "language_code",
        "name": "language_name_de",
        "language_name": "language_name_de",
        "name_de": "language_name_de",
        "display_name_de": "language_name_de",
        "german_name": "language_name_de",
        "de_name": "language_name_de",
        "native_name": "language_name_native",
        "english_name": "language_name_en",
        "name_en": "language_name_en",
        "is_eu_official": "eu_official",
        "available_in_system": "active_in_system",
        "enabled": "active_in_system",
        "selectable": "active_in_system",
        "created_at": "updated_at",
        "modified_at": "updated_at"
    }

    if low in aliases and aliases[low] in row:
        return row[aliases[low]]

    if meta["notnull"] and meta["default"] is None:
        return default_value_for_column(col, meta["type"])

    return None

def insert_dynamic(con, table, rows):
    metas = table_info(con, table)
    cols = [m["name"] for m in metas]

    for row in rows:
        insert_cols = []
        values = []

        for meta in metas:
            col = meta["name"]
            val = row_value(row, col, meta)
            if val is not None:
                insert_cols.append(col)
                values.append(val)

        if not insert_cols:
            continue

        sql = (
            "INSERT INTO " + q(table) +
            " (" + ", ".join(q(c) for c in insert_cols) + ") VALUES (" +
            ", ".join(["?"] * len(insert_cols)) + ")"
        )
        con.execute(sql, values)

def delete_known(con):
    codes = [x[0] for x in EU24]

    info = table_info(con, "app_languages")
    cols = {c["name"].lower(): c["name"] for c in info}

    if "language_code" in cols:
        con.execute("DELETE FROM app_languages WHERE language_code IN (" + ",".join(["?"] * len(codes)) + ")", codes)
    elif "code" in cols:
        con.execute("DELETE FROM app_languages WHERE code IN (" + ",".join(["?"] * len(codes)) + ")", codes)

    delete_map = [
        ("staff_language_profiles", "staff_key", [x["staff_key"] for x in CONFIG_DATA["staff_defaults"]]),
        ("case_language_profiles", "case_key", [x["case_key"] for x in CONFIG_DATA["case_templates"]]),
        ("case_participant_language_profiles", "participant_profile_key", [x["participant_profile_key"] for x in CONFIG_DATA["participant_templates"]]),
        ("communication_language_rules", "rule_key", [x["rule_key"] for x in CONFIG_DATA["communication_rules"]])
    ]

    for table, key, vals in delete_map:
        if not vals:
            continue
        cols2 = {c["name"].lower(): c["name"] for c in table_info(con, table)}
        if key.lower() in cols2:
            con.execute("DELETE FROM " + q(table) + " WHERE " + q(cols2[key.lower()]) + " IN (" + ",".join(["?"] * len(vals)) + ")", vals)

def language_rows():
    rows = []
    for code, de, native, en in EU24:
        rows.append({
            "language_code": code,
            "language_name_de": de,
            "german_name": de,
            "language_name_native": native,
            "language_name_en": en,
            "eu_official": True,
            "active_in_system": True,
            "default_enabled": code in {"de", "en", "sv"},
            "notes": "EU-Amtssprache. Im System verfügbar; tatsächliche Nutzung wird über Profile gesteuert.",
            "updated_at": NOW()
        })
    return rows

def staff_rows():
    rows = []
    for s in CONFIG_DATA["staff_defaults"]:
        rows.append({
            "staff_key": s["staff_key"],
            "role_key": s["role_key"],
            "display_name": s["display_name"],
            "internal_work_language_code": s["internal_work_language_code"],
            "accepted_matter_languages_json": json.dumps(s["accepted_matter_languages"], ensure_ascii=False),
            "communication_languages_json": json.dumps(s["communication_languages"], ensure_ascii=False),
            "document_review_languages_json": json.dumps(s["document_review_languages"], ensure_ascii=False),
            "default_translation_target_language_code": s["default_translation_target_language_code"],
            "active": bool(s["active"]),
            "notes": s["notes"],
            "updated_at": NOW()
        })
    return rows

def case_rows():
    rows = []
    for c in CONFIG_DATA["case_templates"]:
        r = dict(c)
        r["updated_at"] = NOW()
        rows.append(r)
    return rows

def participant_rows():
    rows = []
    for p in CONFIG_DATA["participant_templates"]:
        r = dict(p)
        r["updated_at"] = NOW()
        rows.append(r)
    return rows

def rule_rows():
    rows = []
    for r0 in CONFIG_DATA["communication_rules"]:
        r = dict(r0)
        r["updated_at"] = NOW()
        rows.append(r)
    return rows

def audit(con, status, details):
    row = {
        "audit_id": str(uuid.uuid4()),
        "audit_time": NOW(),
        "audit_area": "language_context_person_case_communication_v1",
        "audit_status": status,
        "details": details
    }
    insert_dynamic(con, "language_profile_audit", [row])

def verify(con):
    eu_count = con.execute(
        "SELECT COUNT(*) FROM app_languages WHERE language_code IN (" + ",".join(["?"] * len(EU24)) + ")",
        [x[0] for x in EU24]
    ).fetchone()[0]

    active_count = con.execute(
        "SELECT COUNT(*) FROM app_languages WHERE active_in_system = TRUE"
    ).fetchone()[0]

    staff_count = con.execute("SELECT COUNT(*) FROM staff_language_profiles").fetchone()[0]
    case_count = con.execute("SELECT COUNT(*) FROM case_language_profiles").fetchone()[0]
    part_count = con.execute("SELECT COUNT(*) FROM case_participant_language_profiles").fetchone()[0]
    rule_count = con.execute("SELECT COUNT(*) FROM communication_language_rules").fetchone()[0]

    se_case = con.execute("""
        SELECT case_key, jurisdiction_country_code, country_language_code, procedural_language_code,
               internal_work_language_code, opponent_lawyer_default_language_code, court_default_language_code
        FROM case_language_profiles
        WHERE case_key = 'TEMPLATE_SE_ARBEITSRECHT'
    """).fetchone()

    court = con.execute("""
        SELECT communication_language_code, document_language_code, procedural_language_code
        FROM case_participant_language_profiles
        WHERE participant_profile_key = 'TEMPLATE_SE_ARBEITSRECHT_GERICHT'
    """).fetchone()

    opponent_lawyer = con.execute("""
        SELECT communication_language_code, document_language_code, procedural_language_code
        FROM case_participant_language_profiles
        WHERE participant_profile_key = 'TEMPLATE_SE_ARBEITSRECHT_GEGNER_ANWALT'
    """).fetchone()

    client = con.execute("""
        SELECT mandate_accepted, communication_language_code, procedural_language_code
        FROM case_participant_language_profiles
        WHERE participant_profile_key = 'TEMPLATE_SE_ARBEITSRECHT_MANDANT'
    """).fetchone()

    if eu_count != 24:
        raise RuntimeError("EU24-Sprachen unvollständig: " + str(eu_count))

    if active_count < 24:
        raise RuntimeError("Nicht alle EU-Sprachen sind im System aktiv verfügbar: " + str(active_count))

    expected_case = ("TEMPLATE_SE_ARBEITSRECHT", "SE", "sv", "sv", "de", "en", "sv")
    if tuple(se_case) != expected_case:
        raise RuntimeError("Schweden-Arbeitsrecht-Fallprofil fehlerhaft: " + repr(se_case))

    if tuple(court) != ("sv", "sv", "sv"):
        raise RuntimeError("Gerichtsprofil fehlerhaft: " + repr(court))

    if tuple(opponent_lawyer) != ("en", "sv", "sv"):
        raise RuntimeError("Profil gegnerischer Anwalt fehlerhaft: " + repr(opponent_lawyer))

    if tuple(client) != (False, "de", "sv"):
        raise RuntimeError("Mandanten-Vorprofil fehlerhaft: " + repr(client))

    return {
        "eu_count": eu_count,
        "active_count": active_count,
        "staff_count": staff_count,
        "case_count": case_count,
        "participant_count": part_count,
        "rule_count": rule_count,
        "se_case": tuple(se_case),
        "court": tuple(court),
        "opponent_lawyer": tuple(opponent_lawyer),
        "client": tuple(client)
    }

def apply():
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    con = duckdb.connect(str(DB))
    try:
        ensure_schema(con)
        delete_known(con)

        insert_dynamic(con, "app_languages", language_rows())
        insert_dynamic(con, "staff_language_profiles", staff_rows())
        insert_dynamic(con, "case_language_profiles", case_rows())
        insert_dynamic(con, "case_participant_language_profiles", participant_rows())
        insert_dynamic(con, "communication_language_rules", rule_rows())

        result = verify(con)
        audit(con, "OK", json.dumps(result, ensure_ascii=False))
        con.commit()
        return result
    except Exception as exc:
        try:
            audit(con, "FEHLER", repr(exc))
            con.commit()
        except Exception:
            pass
        raise
    finally:
        con.close()

def check_only():
    con = duckdb.connect(str(DB), read_only=True)
    try:
        return verify(con)
    finally:
        con.close()

def main():
    if "--check-only" in sys.argv:
        result = check_only()
        print("")
        print("SPRACHKONTEXT CHECK OK")
    else:
        result = apply()
        print("")
        print("SPRACHKONTEXT ANGELEGT")

    print("EU24:", result["eu_count"])
    print("Aktiv verfügbar:", result["active_count"])
    print("Personalprofile:", result["staff_count"])
    print("Fallprofile:", result["case_count"])
    print("Beteiligtenprofile:", result["participant_count"])
    print("Kommunikationsregeln:", result["rule_count"])
    print("Schweden-Arbeitsrecht:", result["se_case"])
    print("Gericht:", result["court"])
    print("Gegnerischer Anwalt:", result["opponent_lawyer"])
    print("Mandant Vorlage:", result["client"])
    print("Konfiguration:", CONFIG)

if __name__ == "__main__":
    try:
        main()
        print("")
        print("Zurück zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(0)
    except KeyboardInterrupt:
        print("")
        print("ABGEBROCHEN DURCH STRG+C")
        print("Zurück zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(130)
    except Exception as exc:
        print("")
        print("FEHLER")
        print(repr(exc))
        print("Zurück zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(1)
