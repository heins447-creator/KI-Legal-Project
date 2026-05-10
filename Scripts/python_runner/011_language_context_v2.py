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
CONFIG = ROOT / "Config" / "language_context_v2.json"

LANGUAGES_EU24 = [
    {"code": "bg", "de": "Bulgarisch", "native": "български"},
    {"code": "hr", "de": "Kroatisch", "native": "hrvatski"},
    {"code": "cs", "de": "Tschechisch", "native": "čeština"},
    {"code": "da", "de": "Dänisch", "native": "dansk"},
    {"code": "nl", "de": "Niederländisch", "native": "Nederlands"},
    {"code": "en", "de": "Englisch", "native": "English"},
    {"code": "et", "de": "Estnisch", "native": "eesti"},
    {"code": "fi", "de": "Finnisch", "native": "suomi"},
    {"code": "fr", "de": "Französisch", "native": "français"},
    {"code": "de", "de": "Deutsch", "native": "Deutsch"},
    {"code": "el", "de": "Griechisch", "native": "ελληνικά"},
    {"code": "hu", "de": "Ungarisch", "native": "magyar"},
    {"code": "ga", "de": "Irisch", "native": "Gaeilge"},
    {"code": "it", "de": "Italienisch", "native": "italiano"},
    {"code": "lv", "de": "Lettisch", "native": "latviešu"},
    {"code": "lt", "de": "Litauisch", "native": "lietuvių"},
    {"code": "mt", "de": "Maltesisch", "native": "Malti"},
    {"code": "pl", "de": "Polnisch", "native": "polski"},
    {"code": "pt", "de": "Portugiesisch", "native": "português"},
    {"code": "ro", "de": "Rumänisch", "native": "română"},
    {"code": "sk", "de": "Slowakisch", "native": "slovenčina"},
    {"code": "sl", "de": "Slowenisch", "native": "slovenščina"},
    {"code": "es", "de": "Spanisch", "native": "español"},
    {"code": "sv", "de": "Schwedisch", "native": "svenska"}
]

STAFF_SETTINGS = [
    {
        "staff_profile_key": "LAWYER_DEFAULT",
        "role_key": "anwalt",
        "display_name": "Anwalt",
        "internal_work_language_code": "de",
        "accepted_matter_languages": ["de", "en", "sv"],
        "communication_languages": ["de", "en", "sv"],
        "document_review_languages": ["de", "en", "sv"],
        "default_draft_language_code": "de",
        "default_translation_target_language_code": "de",
        "can_accept_foreign_mandates": True,
        "active": True,
        "notes": "Grundeinstellung. Der Anwalt arbeitet intern deutsch und wählt selbst, in welchen Sprachen er Aufträge annimmt und kommuniziert."
    },
    {
        "staff_profile_key": "SECRETARY_DEFAULT",
        "role_key": "sekretariat",
        "display_name": "Sekretariat",
        "internal_work_language_code": "de",
        "accepted_matter_languages": ["de", "en", "sv"],
        "communication_languages": ["de", "en"],
        "document_review_languages": ["de", "en", "sv"],
        "default_draft_language_code": "de",
        "default_translation_target_language_code": "de",
        "can_accept_foreign_mandates": False,
        "active": True,
        "notes": "Grundeinstellung für Vorzimmer, Posteingang und vorbereitende Kommunikation."
    }
]

CASE_SETTINGS = [
    {
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "case_label": "Schweden Arbeitsrecht",
        "jurisdiction_country_code": "SE",
        "legal_area_key": "arbeitsrecht",
        "country_language_code": "sv",
        "procedural_language_code": "sv",
        "internal_work_language_code": "de",
        "default_document_language_code": "sv",
        "default_actual_language_code": "sv",
        "translation_required_default": True,
        "interpreter_required_default": False,
        "notes": "Schwedischer Arbeitsrechtsfall. Landessprache und Prozesssprache Schwedisch. Interne Arbeitssprache Deutsch."
    }
]

PARTICIPANT_SETTINGS = [
    {
        "participant_profile_key": "SE_ARBEITSRECHT_GERICHT",
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "participant_role": "gericht",
        "participant_label": "Schwedisches Gericht",
        "official_or_procedural_language_code": "sv",
        "communication_language_code": "sv",
        "document_language_code": "sv",
        "actual_or_spoken_language_code": "sv",
        "fallback_language_code": "en",
        "translation_required": True,
        "created_after_mandate_acceptance": False,
        "accepted_client_required": False,
        "notes": "Gerichtliche Kommunikation und Schriftsätze in schwedischer Prozesssprache."
    },
    {
        "participant_profile_key": "SE_ARBEITSRECHT_GEGNER_ANWALT",
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "participant_role": "gegnerischer_anwalt",
        "participant_label": "Gegnerischer Anwalt",
        "official_or_procedural_language_code": "sv",
        "communication_language_code": "en",
        "document_language_code": "sv",
        "actual_or_spoken_language_code": "en",
        "fallback_language_code": "sv",
        "translation_required": True,
        "created_after_mandate_acceptance": False,
        "accepted_client_required": False,
        "notes": "Kommunikation kann Englisch sein. Maßgebliche Verfahrens- und Dokumentensprache bleibt Schwedisch."
    },
    {
        "participant_profile_key": "SE_ARBEITSRECHT_GEGENSEITE",
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "participant_role": "gegenseite",
        "participant_label": "Gegenseite",
        "official_or_procedural_language_code": "sv",
        "communication_language_code": "sv",
        "document_language_code": "sv",
        "actual_or_spoken_language_code": "sv",
        "fallback_language_code": "en",
        "translation_required": True,
        "created_after_mandate_acceptance": False,
        "accepted_client_required": False,
        "notes": "Gegenseite grundsätzlich in der Landessprache und Verfahrenssprache."
    },
    {
        "participant_profile_key": "SE_ARBEITSRECHT_MANDANT_NACH_ANNAHME",
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "participant_role": "mandant",
        "participant_label": "Mandant nach Mandatsannahme",
        "official_or_procedural_language_code": "sv",
        "communication_language_code": "de",
        "document_language_code": "de",
        "actual_or_spoken_language_code": "de",
        "fallback_language_code": "en",
        "translation_required": True,
        "created_after_mandate_acceptance": True,
        "accepted_client_required": True,
        "notes": "Mandantenbezogene Spracheinstellungen werden erst nach Annahme des Mandats als echtes Mandantenprofil angelegt."
    },
    {
        "participant_profile_key": "SE_ARBEITSRECHT_INTERN",
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "participant_role": "intern",
        "participant_label": "Interne Bearbeitung",
        "official_or_procedural_language_code": "de",
        "communication_language_code": "de",
        "document_language_code": "de",
        "actual_or_spoken_language_code": "de",
        "fallback_language_code": "en",
        "translation_required": False,
        "created_after_mandate_acceptance": False,
        "accepted_client_required": False,
        "notes": "Interne Bearbeitung und Arbeitsvermerke deutsch."
    }
]

INTAKE_RULES = [
    {
        "intake_rule_key": "POSTEINGANG_SE_ARBEITSRECHT",
        "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
        "incoming_area": "posteingang",
        "expected_document_language_code": "sv",
        "detected_language_policy": "dokumentensprache_ermitteln_und_mit_fallprofil_abgleichen",
        "target_internal_language_code": "de",
        "procedural_language_code": "sv",
        "action_on_mismatch": "entscheidungskarte_fuer_vorzimmer_und_uebersetzungsbedarf_markieren",
        "notes": "Beim Datenimport werden Dokumentensprache, tatsächlich erkannte Sprache, interne Arbeitssprache und Prozesssprache getrennt geführt."
    }
]

CONFIG_DATA = {
    "version": "V2_NEUANFANG",
    "available_languages": "EU24",
    "principle": "Sprachen werden getrennt nach Systemkatalog, Person, Fall, Beteiligtem, Kommunikation, Dokument und tatsächlicher Sprache geführt.",
    "staff_settings": STAFF_SETTINGS,
    "case_settings": CASE_SETTINGS,
    "participant_settings": PARTICIPANT_SETTINGS,
    "intake_rules": INTAKE_RULES
}

DDL = [
    "DROP TABLE IF EXISTS lang_language_catalog",
    "DROP TABLE IF EXISTS lang_staff_language_settings",
    "DROP TABLE IF EXISTS lang_case_language_settings",
    "DROP TABLE IF EXISTS lang_participant_language_settings",
    "DROP TABLE IF EXISTS lang_intake_language_rules",
    "DROP TABLE IF EXISTS lang_language_context_audit",
    """
    CREATE TABLE lang_language_catalog (
        language_code VARCHAR PRIMARY KEY,
        language_name_de VARCHAR NOT NULL,
        language_name_native VARCHAR,
        iso_639_1 VARCHAR,
        eu_official BOOLEAN,
        available_in_system BOOLEAN,
        selectable_for_staff BOOLEAN,
        selectable_for_case BOOLEAN,
        default_enabled BOOLEAN,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE lang_staff_language_settings (
        staff_profile_key VARCHAR PRIMARY KEY,
        role_key VARCHAR,
        display_name VARCHAR,
        internal_work_language_code VARCHAR,
        accepted_matter_languages_json VARCHAR,
        communication_languages_json VARCHAR,
        document_review_languages_json VARCHAR,
        default_draft_language_code VARCHAR,
        default_translation_target_language_code VARCHAR,
        can_accept_foreign_mandates BOOLEAN,
        active BOOLEAN,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE lang_case_language_settings (
        case_template_key VARCHAR PRIMARY KEY,
        case_label VARCHAR,
        jurisdiction_country_code VARCHAR,
        legal_area_key VARCHAR,
        country_language_code VARCHAR,
        procedural_language_code VARCHAR,
        internal_work_language_code VARCHAR,
        default_document_language_code VARCHAR,
        default_actual_language_code VARCHAR,
        translation_required_default BOOLEAN,
        interpreter_required_default BOOLEAN,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE lang_participant_language_settings (
        participant_profile_key VARCHAR PRIMARY KEY,
        case_template_key VARCHAR,
        participant_role VARCHAR,
        participant_label VARCHAR,
        official_or_procedural_language_code VARCHAR,
        communication_language_code VARCHAR,
        document_language_code VARCHAR,
        actual_or_spoken_language_code VARCHAR,
        fallback_language_code VARCHAR,
        translation_required BOOLEAN,
        created_after_mandate_acceptance BOOLEAN,
        accepted_client_required BOOLEAN,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE lang_intake_language_rules (
        intake_rule_key VARCHAR PRIMARY KEY,
        case_template_key VARCHAR,
        incoming_area VARCHAR,
        expected_document_language_code VARCHAR,
        detected_language_policy VARCHAR,
        target_internal_language_code VARCHAR,
        procedural_language_code VARCHAR,
        action_on_mismatch VARCHAR,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE lang_language_context_audit (
        audit_id VARCHAR PRIMARY KEY,
        audit_time TIMESTAMP,
        audit_area VARCHAR,
        audit_status VARCHAR,
        details VARCHAR
    )
    """
]

def insert_language_catalog(con):
    for item in LANGUAGES_EU24:
        con.execute(
            """
            INSERT INTO lang_language_catalog
            (language_code, language_name_de, language_name_native, iso_639_1,
             eu_official, available_in_system, selectable_for_staff, selectable_for_case,
             default_enabled, notes, updated_at)
            VALUES (?, ?, ?, ?, TRUE, TRUE, TRUE, TRUE, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                item["code"],
                item["de"],
                item["native"],
                item["code"],
                item["code"] in {"de", "en", "sv"},
                "EU-Amtssprache. Im System verfügbar; konkrete Nutzung wird über Personen- und Fallprofil gewählt."
            ]
        )

def insert_staff(con):
    for s in STAFF_SETTINGS:
        con.execute(
            """
            INSERT INTO lang_staff_language_settings
            (staff_profile_key, role_key, display_name, internal_work_language_code,
             accepted_matter_languages_json, communication_languages_json,
             document_review_languages_json, default_draft_language_code,
             default_translation_target_language_code, can_accept_foreign_mandates,
             active, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                s["staff_profile_key"],
                s["role_key"],
                s["display_name"],
                s["internal_work_language_code"],
                json.dumps(s["accepted_matter_languages"], ensure_ascii=False),
                json.dumps(s["communication_languages"], ensure_ascii=False),
                json.dumps(s["document_review_languages"], ensure_ascii=False),
                s["default_draft_language_code"],
                s["default_translation_target_language_code"],
                bool(s["can_accept_foreign_mandates"]),
                bool(s["active"]),
                s["notes"]
            ]
        )

def insert_cases(con):
    for c in CASE_SETTINGS:
        con.execute(
            """
            INSERT INTO lang_case_language_settings
            (case_template_key, case_label, jurisdiction_country_code, legal_area_key,
             country_language_code, procedural_language_code, internal_work_language_code,
             default_document_language_code, default_actual_language_code,
             translation_required_default, interpreter_required_default, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                c["case_template_key"],
                c["case_label"],
                c["jurisdiction_country_code"],
                c["legal_area_key"],
                c["country_language_code"],
                c["procedural_language_code"],
                c["internal_work_language_code"],
                c["default_document_language_code"],
                c["default_actual_language_code"],
                bool(c["translation_required_default"]),
                bool(c["interpreter_required_default"]),
                c["notes"]
            ]
        )

def insert_participants(con):
    for p in PARTICIPANT_SETTINGS:
        con.execute(
            """
            INSERT INTO lang_participant_language_settings
            (participant_profile_key, case_template_key, participant_role, participant_label,
             official_or_procedural_language_code, communication_language_code,
             document_language_code, actual_or_spoken_language_code, fallback_language_code,
             translation_required, created_after_mandate_acceptance, accepted_client_required,
             notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                p["participant_profile_key"],
                p["case_template_key"],
                p["participant_role"],
                p["participant_label"],
                p["official_or_procedural_language_code"],
                p["communication_language_code"],
                p["document_language_code"],
                p["actual_or_spoken_language_code"],
                p["fallback_language_code"],
                bool(p["translation_required"]),
                bool(p["created_after_mandate_acceptance"]),
                bool(p["accepted_client_required"]),
                p["notes"]
            ]
        )

def insert_intake_rules(con):
    for r in INTAKE_RULES:
        con.execute(
            """
            INSERT INTO lang_intake_language_rules
            (intake_rule_key, case_template_key, incoming_area, expected_document_language_code,
             detected_language_policy, target_internal_language_code, procedural_language_code,
             action_on_mismatch, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                r["intake_rule_key"],
                r["case_template_key"],
                r["incoming_area"],
                r["expected_document_language_code"],
                r["detected_language_policy"],
                r["target_internal_language_code"],
                r["procedural_language_code"],
                r["action_on_mismatch"],
                r["notes"]
            ]
        )

def audit(con, status, details):
    con.execute(
        """
        INSERT INTO lang_language_context_audit
        (audit_id, audit_time, audit_area, audit_status, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            "language_context_v2",
            status,
            details
        ]
    )

def verify(con):
    language_count = con.execute("SELECT COUNT(*) FROM lang_language_catalog WHERE eu_official = TRUE").fetchone()[0]
    staff_count = con.execute("SELECT COUNT(*) FROM lang_staff_language_settings").fetchone()[0]
    case_count = con.execute("SELECT COUNT(*) FROM lang_case_language_settings").fetchone()[0]
    participant_count = con.execute("SELECT COUNT(*) FROM lang_participant_language_settings").fetchone()[0]
    intake_count = con.execute("SELECT COUNT(*) FROM lang_intake_language_rules").fetchone()[0]

    if language_count != 24:
        raise RuntimeError("EU24-Sprachkatalog unvollständig: " + str(language_count))

    row = con.execute(
        """
        SELECT jurisdiction_country_code, country_language_code, procedural_language_code,
               internal_work_language_code, default_document_language_code, default_actual_language_code
        FROM lang_case_language_settings
        WHERE case_template_key = 'TEMPLATE_SE_ARBEITSRECHT'
        """
    ).fetchone()

    expected = ("SE", "sv", "sv", "de", "sv", "sv")

    if tuple(row or ()) != expected:
        raise RuntimeError("Schweden-Arbeitsrecht-Sprachprofil fehlerhaft: " + repr(row))

    opponent = con.execute(
        """
        SELECT communication_language_code, document_language_code, actual_or_spoken_language_code
        FROM lang_participant_language_settings
        WHERE participant_profile_key = 'SE_ARBEITSRECHT_GEGNER_ANWALT'
        """
    ).fetchone()

    if tuple(opponent or ()) != ("en", "sv", "en"):
        raise RuntimeError("Gegnerischer Anwalt Sprachprofil fehlerhaft: " + repr(opponent))

    client_template = con.execute(
        """
        SELECT created_after_mandate_acceptance, accepted_client_required
        FROM lang_participant_language_settings
        WHERE participant_profile_key = 'SE_ARBEITSRECHT_MANDANT_NACH_ANNAHME'
        """
    ).fetchone()

    if tuple(client_template or ()) != (True, True):
        raise RuntimeError("Mandanten-Sprachprofil ist nicht an Mandatsannahme gebunden: " + repr(client_template))

    return {
        "eu24_languages": language_count,
        "staff_profiles": staff_count,
        "case_profiles": case_count,
        "participant_profiles": participant_count,
        "intake_rules": intake_count,
        "se_case_profile": row,
        "opponent_lawyer_profile": opponent,
        "client_after_acceptance": client_template
    }

def main():
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(
        json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n"
    )

    con = duckdb.connect(str(DB))

    try:
        con.execute("BEGIN TRANSACTION")

        for sql in DDL:
            con.execute(sql)

        insert_language_catalog(con)
        insert_staff(con)
        insert_cases(con)
        insert_participants(con)
        insert_intake_rules(con)

        result = verify(con)
        audit(con, "OK", json.dumps(result, ensure_ascii=False))

        con.execute("COMMIT")

    except Exception as exc:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise

    finally:
        con.close()

    print("")
    print("SPRACHKONTEXT V2 NEUANFANG FERTIG")
    print("EU24-Sprachen:", result["eu24_languages"])
    print("Personalprofile:", result["staff_profiles"])
    print("Fallprofile:", result["case_profiles"])
    print("Beteiligtenprofile:", result["participant_profiles"])
    print("Posteingangsregeln:", result["intake_rules"])
    print("Schweden-Arbeitsrecht:", result["se_case_profile"])
    print("Gegnerischer Anwalt:", result["opponent_lawyer_profile"])
    print("Mandant erst nach Annahme:", result["client_after_acceptance"])
    print("Konfiguration:", CONFIG)

if __name__ == "__main__":
    try:
        main()
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
