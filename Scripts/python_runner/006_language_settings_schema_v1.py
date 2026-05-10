# -*- coding: utf-8 -*-
import sys
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import duckdb
except Exception as exc:
    print("FEHLER: DuckDB-Modul konnte nicht geladen werden:", repr(exc))
    raise

DB = Path(sys.argv[1])
REPORT = Path(sys.argv[2])

def w(text=""):
    line = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + str(text)
    print(line)
    with open(REPORT, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")

EU_LANGUAGES = [
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

SCHEMA_SQL = [
    "CREATE TABLE IF NOT EXISTS app_languages (language_code VARCHAR PRIMARY KEY, german_name VARCHAR NOT NULL, native_name VARCHAR, english_name VARCHAR, eu_official BOOLEAN NOT NULL DEFAULT true, active_in_system BOOLEAN NOT NULL DEFAULT true, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS software_language_settings (setting_key VARCHAR PRIMARY KEY, default_ui_language_code VARCHAR NOT NULL, default_internal_work_language_code VARCHAR NOT NULL, fallback_translation_language_code VARCHAR NOT NULL, require_case_language_profile BOOLEAN NOT NULL DEFAULT true, notes VARCHAR, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS role_language_settings (role_key VARCHAR PRIMARY KEY, role_display_name VARCHAR NOT NULL, ui_language_code VARCHAR NOT NULL, internal_work_language_code VARCHAR NOT NULL, notes VARCHAR, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS role_mandate_languages (role_key VARCHAR NOT NULL, language_code VARCHAR NOT NULL, accepts_mandates BOOLEAN NOT NULL DEFAULT false, accepts_communication BOOLEAN NOT NULL DEFAULT false, notes VARCHAR, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(role_key, language_code))",
    "CREATE TABLE IF NOT EXISTS case_language_profiles (case_key VARCHAR PRIMARY KEY, case_name VARCHAR NOT NULL, jurisdiction_country_code VARCHAR NOT NULL, jurisdiction_name VARCHAR NOT NULL, law_area VARCHAR NOT NULL, national_language_code VARCHAR NOT NULL, procedural_language_code VARCHAR NOT NULL, internal_work_language_code VARCHAR NOT NULL, client_communication_language_code VARCHAR, opponent_communication_language_code VARCHAR, opponent_lawyer_language_code VARCHAR, translation_required BOOLEAN NOT NULL DEFAULT true, notes VARCHAR, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE IF NOT EXISTS posteingang_language_profiles (intake_id VARCHAR PRIMARY KEY, original_name VARCHAR, declared_language_code VARCHAR, detected_language_code VARCHAR, jurisdiction_country_code VARCHAR, procedural_language_code VARCHAR, internal_work_language_code VARCHAR, translation_required BOOLEAN, confidence VARCHAR, notes VARCHAR, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
]

def main():
    w("Python-Sprachschema V1 beginnt.")
    w("Datenbank: " + str(DB))

    con = duckdb.connect(str(DB))

    try:
        con.execute("BEGIN TRANSACTION")

        for sql in SCHEMA_SQL:
            con.execute(sql)

        con.execute("DELETE FROM app_languages WHERE eu_official = TRUE")
        con.executemany(
            "INSERT INTO app_languages (language_code, german_name, native_name, english_name, eu_official, active_in_system, updated_at) VALUES (?, ?, ?, ?, TRUE, TRUE, CURRENT_TIMESTAMP)",
            EU_LANGUAGES
        )

        con.execute("DELETE FROM software_language_settings WHERE setting_key = 'default'")
        con.execute(
            "INSERT INTO software_language_settings (setting_key, default_ui_language_code, default_internal_work_language_code, fallback_translation_language_code, require_case_language_profile, notes, updated_at) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            [
                "default",
                "de",
                "de",
                "de",
                True,
                "Grundeinstellung: Oberfläche und interne Arbeit zunächst Deutsch. Jeder Fall erhält ein eigenes Sprachprofil."
            ]
        )

        con.execute("DELETE FROM role_language_settings WHERE role_key IN ('anwalt', 'sekretariat')")
        con.executemany(
            "INSERT INTO role_language_settings (role_key, role_display_name, ui_language_code, internal_work_language_code, notes, updated_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            [
                ("anwalt", "Anwalt", "de", "de", "Der Anwalt kann Arbeits- und Annahmesprachen gesondert auswählen."),
                ("sekretariat", "Sekretariat", "de", "de", "Das Sekretariat arbeitet im Ausgangszustand deutsch und bereitet fremdsprachige Eingänge vor.")
            ]
        )

        con.execute("DELETE FROM role_mandate_languages WHERE role_key IN ('anwalt', 'sekretariat')")

        default_accept = {
            "anwalt": {"de", "en", "sv"},
            "sekretariat": set()
        }

        default_comm = {
            "anwalt": {"de", "en", "sv"},
            "sekretariat": {"de", "en", "sv"}
        }

        rows = []
        for role_key in ["anwalt", "sekretariat"]:
            for code, german_name, native_name, english_name in EU_LANGUAGES:
                rows.append((
                    role_key,
                    code,
                    code in default_accept[role_key],
                    code in default_comm[role_key],
                    "Sprache ist im System vorhanden. Annahme und Kommunikation sind einstellbar."
                ))

        con.executemany(
            "INSERT INTO role_mandate_languages (role_key, language_code, accepts_mandates, accepts_communication, notes, updated_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            rows
        )

        con.execute("DELETE FROM case_language_profiles WHERE case_key = 'TEMPLATE_SE_ARBEITSRECHT'")
        con.execute(
            "INSERT INTO case_language_profiles (case_key, case_name, jurisdiction_country_code, jurisdiction_name, law_area, national_language_code, procedural_language_code, internal_work_language_code, client_communication_language_code, opponent_communication_language_code, opponent_lawyer_language_code, translation_required, notes, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            [
                "TEMPLATE_SE_ARBEITSRECHT",
                "Vorlage Schweden Arbeitsrecht",
                "SE",
                "Schweden",
                "Arbeitsrecht",
                "sv",
                "sv",
                "de",
                "de",
                "sv",
                "en",
                True,
                "Landessprache und Prozeßsprache Schwedisch. Interne Arbeit Deutsch. Kommunikation mit gegnerischem Anwalt kann Englisch sein."
            ]
        )

        con.execute("COMMIT")

    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise

    count = con.execute("SELECT COUNT(*) FROM app_languages WHERE eu_official = TRUE").fetchone()[0]
    if count != 24:
        raise RuntimeError("EU24-Sprachen nicht vollständig. Gefunden: " + str(count))

    template = con.execute("SELECT case_key, jurisdiction_country_code, procedural_language_code, internal_work_language_code, opponent_lawyer_language_code FROM case_language_profiles WHERE case_key = 'TEMPLATE_SE_ARBEITSRECHT'").fetchone()
    if not template:
        raise RuntimeError("Schweden-Arbeitsrecht-Vorlage fehlt.")

    w("EU24-Sprachen angelegt: " + str(count))
    w("Schweden-Arbeitsrecht-Vorlage: " + repr(template))
    w("Python-Sprachschema V1 abgeschlossen.")

    con.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
        print("ABGEBROCHEN DURCH STRG+C")
        sys.exit(130)
