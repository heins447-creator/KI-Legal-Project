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
CONFIG = ROOT / "Config" / "vorzimmer_kommunikationsparameter_v1.json"

EU24 = [
    ("bg", "Bulgarisch"),
    ("hr", "Kroatisch"),
    ("cs", "Tschechisch"),
    ("da", "Dänisch"),
    ("nl", "Niederländisch"),
    ("en", "Englisch"),
    ("et", "Estnisch"),
    ("fi", "Finnisch"),
    ("fr", "Französisch"),
    ("de", "Deutsch"),
    ("el", "Griechisch"),
    ("hu", "Ungarisch"),
    ("ga", "Irisch"),
    ("it", "Italienisch"),
    ("lv", "Lettisch"),
    ("lt", "Litauisch"),
    ("mt", "Maltesisch"),
    ("pl", "Polnisch"),
    ("pt", "Portugiesisch"),
    ("ro", "Rumänisch"),
    ("sk", "Slowakisch"),
    ("sl", "Slowenisch"),
    ("es", "Spanisch"),
    ("sv", "Schwedisch"),
]

DDL = [
    """
    CREATE TABLE IF NOT EXISTS vz_language_package_catalog (
        language_code VARCHAR PRIMARY KEY,
        language_name_de VARCHAR,
        eu_official BOOLEAN,
        available BOOLEAN,
        default_target_for_work_translation BOOLEAN,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vz_communication_context_template (
        template_key VARCHAR PRIMARY KEY,
        case_type VARCHAR,
        jurisdiction_country_code VARCHAR,
        official_language_code VARCHAR,
        procedural_language_code VARCHAR,
        internal_work_language_code VARCHAR,
        rough_translation_target_language_code VARCHAR,
        default_document_language_code VARCHAR,
        notes VARCHAR,
        editable BOOLEAN,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vz_participant_communication_profile (
        profile_key VARCHAR PRIMARY KEY,
        template_key VARCHAR,
        participant_role VARCHAR,
        participant_label VARCHAR,
        country_code VARCHAR,
        expected_language_code VARCHAR,
        communication_language_code VARCHAR,
        document_language_code VARCHAR,
        rough_translation_target_language_code VARCHAR,
        created_after_mandate_acceptance BOOLEAN,
        accepted_client_required BOOLEAN,
        editable BOOLEAN,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vz_address_language_inference_rule (
        rule_key VARCHAR PRIMARY KEY,
        country_code VARCHAR,
        postal_code_prefix VARCHAR,
        address_contains VARCHAR,
        language_code VARCHAR,
        confidence_level VARCHAR,
        notes VARCHAR,
        active BOOLEAN,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vz_communication_parameter_audit (
        audit_id VARCHAR PRIMARY KEY,
        audit_time TIMESTAMP,
        audit_area VARCHAR,
        audit_status VARCHAR,
        details VARCHAR
    )
    """,
]

CONFIG_DATA = {
    "version": "V1",
    "principle": "Das Vorzimmer pflegt Kommunikations- und Sprachgrundparameter. Inhaltliche Beweis- oder Rechtsbewertung erfolgt nachgelagert.",
    "default_internal_work_language": "de",
    "default_rough_translation_target": "de",
    "templates": [
        {
            "template_key": "TEMPLATE_SE_ARBEITSRECHT",
            "case_type": "Arbeitsrechtsstreit Arbeitnehmer gegen kommunalen Arbeitgeber in Schweden",
            "jurisdiction_country_code": "SE",
            "official_language_code": "sv",
            "procedural_language_code": "sv",
            "internal_work_language_code": "de",
            "rough_translation_target_language_code": "de",
            "default_document_language_code": "sv",
            "notes": "Schwedischer Arbeitsrechtsfall. Amtssprache und Prozeßsprache Schwedisch. Interne Arbeitssprache des bearbeitenden Anwalts Deutsch.",
            "editable": True
        }
    ],
    "participant_profiles": [
        {
            "profile_key": "SE_ARBEITSRECHT_GERICHT",
            "template_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gericht",
            "participant_label": "Schwedisches Gericht",
            "country_code": "SE",
            "expected_language_code": "sv",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "rough_translation_target_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "editable": True,
            "notes": "Gerichtliche Kommunikation in schwedischer Prozeßsprache."
        },
        {
            "profile_key": "SE_ARBEITSRECHT_ARBEITGEBER",
            "template_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gegenseite",
            "participant_label": "Kommunaler Arbeitgeber Schweden",
            "country_code": "SE",
            "expected_language_code": "sv",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "rough_translation_target_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "editable": True,
            "notes": "Gegenseite im schwedischen Arbeitsrechtsstreit."
        },
        {
            "profile_key": "SE_ARBEITSRECHT_GEGNERISCHER_ANWALT",
            "template_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "gegnerischer_anwalt",
            "participant_label": "Gegnerischer Anwalt",
            "country_code": "SE",
            "expected_language_code": "sv",
            "communication_language_code": "sv",
            "document_language_code": "sv",
            "rough_translation_target_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "editable": True,
            "notes": "Grundregel Schwedisch. Abweichungen können später durch das Vorzimmer eingetragen werden."
        },
        {
            "profile_key": "SE_ARBEITSRECHT_MANDANT_NACH_ANNAHME",
            "template_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "mandant",
            "participant_label": "Mandant nach Mandatsannahme",
            "country_code": "",
            "expected_language_code": "",
            "communication_language_code": "",
            "document_language_code": "",
            "rough_translation_target_language_code": "de",
            "created_after_mandate_acceptance": True,
            "accepted_client_required": True,
            "editable": True,
            "notes": "Mandantenbezogene Spracheinstellungen werden erst nach Mandatsannahme konkret angelegt oder vervollständigt."
        },
        {
            "profile_key": "KANZLEI_INTERN",
            "template_key": "TEMPLATE_SE_ARBEITSRECHT",
            "participant_role": "intern",
            "participant_label": "Interne Bearbeitung Anwalt und Sekretariat",
            "country_code": "DE",
            "expected_language_code": "de",
            "communication_language_code": "de",
            "document_language_code": "de",
            "rough_translation_target_language_code": "de",
            "created_after_mandate_acceptance": False,
            "accepted_client_required": False,
            "editable": True,
            "notes": "Interne Arbeitssprache Deutsch."
        }
    ],
    "address_language_rules": [
        {"rule_key": "COUNTRY_SE_DEFAULT", "country_code": "SE", "postal_code_prefix": "", "address_contains": "", "language_code": "sv", "confidence_level": "hoch", "notes": "Schweden führt zur Sprachvoreinstellung Schwedisch.", "active": True},
        {"rule_key": "COUNTRY_DE_DEFAULT", "country_code": "DE", "postal_code_prefix": "", "address_contains": "", "language_code": "de", "confidence_level": "hoch", "notes": "Deutschland führt zur Sprachvoreinstellung Deutsch.", "active": True},
        {"rule_key": "COUNTRY_AT_DEFAULT", "country_code": "AT", "postal_code_prefix": "", "address_contains": "", "language_code": "de", "confidence_level": "hoch", "notes": "Österreich führt zur Sprachvoreinstellung Deutsch.", "active": True},
        {"rule_key": "COUNTRY_FR_DEFAULT", "country_code": "FR", "postal_code_prefix": "", "address_contains": "", "language_code": "fr", "confidence_level": "hoch", "notes": "Frankreich führt zur Sprachvoreinstellung Französisch.", "active": True},
        {"rule_key": "COUNTRY_ES_DEFAULT", "country_code": "ES", "postal_code_prefix": "", "address_contains": "", "language_code": "es", "confidence_level": "hoch", "notes": "Spanien führt zur Sprachvoreinstellung Spanisch.", "active": True},
        {"rule_key": "COUNTRY_IT_DEFAULT", "country_code": "IT", "postal_code_prefix": "", "address_contains": "", "language_code": "it", "confidence_level": "hoch", "notes": "Italien führt zur Sprachvoreinstellung Italienisch.", "active": True},
        {"rule_key": "ADDRESS_SWEDEN_TEXT", "country_code": "", "postal_code_prefix": "", "address_contains": "Sweden", "language_code": "sv", "confidence_level": "mittel", "notes": "Adresshinweis Sweden.", "active": True},
        {"rule_key": "ADDRESS_SVERIGE_TEXT", "country_code": "", "postal_code_prefix": "", "address_contains": "Sverige", "language_code": "sv", "confidence_level": "hoch", "notes": "Adresshinweis Sverige.", "active": True}
    ]
}

def audit(con, status, details):
    con.execute(
        """
        INSERT INTO vz_communication_parameter_audit
        (audit_id, audit_time, audit_area, audit_status, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
        """,
        [str(uuid.uuid4()), "vorzimmer_kommunikationsparameter_v1", status, details]
    )

def ensure_schema(con):
    for ddl in DDL:
        con.execute(ddl)

def clear_seed(con):
    con.execute("DELETE FROM vz_language_package_catalog")
    con.execute("DELETE FROM vz_communication_context_template WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'")
    con.execute("DELETE FROM vz_participant_communication_profile WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT' OR profile_key = 'KANZLEI_INTERN'")
    con.execute("DELETE FROM vz_address_language_inference_rule")

def seed_languages(con):
    for code, name in EU24:
        con.execute(
            """
            INSERT INTO vz_language_package_catalog
            (language_code, language_name_de, eu_official, available, default_target_for_work_translation, notes, updated_at)
            VALUES (?, ?, TRUE, TRUE, ?, ?, CURRENT_TIMESTAMP)
            """,
            [code, name, code == "de", "EU-Amtssprache als auswählbares Sprachpaket."]
        )

def seed_templates(con):
    for t in CONFIG_DATA["templates"]:
        con.execute(
            """
            INSERT INTO vz_communication_context_template
            (template_key, case_type, jurisdiction_country_code, official_language_code,
             procedural_language_code, internal_work_language_code, rough_translation_target_language_code,
             default_document_language_code, notes, editable, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                t["template_key"], t["case_type"], t["jurisdiction_country_code"],
                t["official_language_code"], t["procedural_language_code"],
                t["internal_work_language_code"], t["rough_translation_target_language_code"],
                t["default_document_language_code"], t["notes"], bool(t["editable"])
            ]
        )

def seed_profiles(con):
    for p in CONFIG_DATA["participant_profiles"]:
        con.execute(
            """
            INSERT INTO vz_participant_communication_profile
            (profile_key, template_key, participant_role, participant_label, country_code,
             expected_language_code, communication_language_code, document_language_code,
             rough_translation_target_language_code, created_after_mandate_acceptance,
             accepted_client_required, editable, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                p["profile_key"], p["template_key"], p["participant_role"], p["participant_label"],
                p["country_code"], p["expected_language_code"], p["communication_language_code"],
                p["document_language_code"], p["rough_translation_target_language_code"],
                bool(p["created_after_mandate_acceptance"]), bool(p["accepted_client_required"]),
                bool(p["editable"]), p["notes"]
            ]
        )

def seed_rules(con):
    for r in CONFIG_DATA["address_language_rules"]:
        con.execute(
            """
            INSERT INTO vz_address_language_inference_rule
            (rule_key, country_code, postal_code_prefix, address_contains, language_code,
             confidence_level, notes, active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                r["rule_key"], r["country_code"], r["postal_code_prefix"], r["address_contains"],
                r["language_code"], r["confidence_level"], r["notes"], bool(r["active"])
            ]
        )

def verify(con):
    eu_count = con.execute("SELECT COUNT(*) FROM vz_language_package_catalog WHERE eu_official = TRUE").fetchone()[0]
    if eu_count != 24:
        raise RuntimeError("EU24-Sprachpakete unvollständig: " + str(eu_count))

    template = con.execute(
        """
        SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
               internal_work_language_code, rough_translation_target_language_code,
               default_document_language_code
        FROM vz_communication_context_template
        WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
        """
    ).fetchone()

    expected = ("SE", "sv", "sv", "de", "de", "sv")
    if tuple(template or ()) != expected:
        raise RuntimeError("Schweden-Arbeitsrecht-Vorzimmerparameter fehlerhaft: " + repr(template))

    external_bad = con.execute(
        """
        SELECT COUNT(*)
        FROM vz_participant_communication_profile
        WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
          AND participant_role IN ('gericht', 'gegenseite', 'gegnerischer_anwalt')
          AND communication_language_code <> 'sv'
        """
    ).fetchone()[0]

    if external_bad != 0:
        raise RuntimeError("Externe Kommunikation ist nicht durchgehend Schwedisch voreingestellt.")

    mandate_placeholder = con.execute(
        """
        SELECT created_after_mandate_acceptance, accepted_client_required
        FROM vz_participant_communication_profile
        WHERE profile_key = 'SE_ARBEITSRECHT_MANDANT_NACH_ANNAHME'
        """
    ).fetchone()

    if tuple(mandate_placeholder or ()) != (True, True):
        raise RuntimeError("Mandantenprofil ist nicht korrekt auf spätere Mandatsannahme gesetzt.")

    return {
        "eu24": eu_count,
        "template": template,
        "external_bad": external_bad,
        "mandate_placeholder": mandate_placeholder,
        "participant_profiles": con.execute("SELECT COUNT(*) FROM vz_participant_communication_profile").fetchone()[0],
        "inference_rules": con.execute("SELECT COUNT(*) FROM vz_address_language_inference_rule").fetchone()[0],
    }

def main():
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    con = duckdb.connect(str(DB))
    try:
        ensure_schema(con)
        clear_seed(con)
        seed_languages(con)
        seed_templates(con)
        seed_profiles(con)
        seed_rules(con)
        result = verify(con)
        audit(con, "OK", json.dumps(result, ensure_ascii=False, default=str))
    except Exception as exc:
        try:
            audit(con, "FEHLER", repr(exc))
        except Exception:
            pass
        raise
    finally:
        con.close()

    print("")
    print("VORZIMMER_KOMMUNIKATIONSPARAMETER_V1 FERTIG")
    print("EU24:", result["eu24"])
    print("Template:", result["template"])
    print("Beteiligtenprofile:", result["participant_profiles"])
    print("Adress-/Sprachregeln:", result["inference_rules"])
    print("Konfiguration:", CONFIG)

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("")
        print("ABGEBROCHEN DURCH STRG+C")
        print("Zurueck zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(130)
    except Exception as exc:
        print("")
        print("FEHLER")
        print(repr(exc))
        print("Zurueck zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(1)
