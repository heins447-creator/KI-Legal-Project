# -*- coding: utf-8 -*-
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import duckdb

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"

def main():
    print("DATENBANKPRUEFUNG NACH POSTEINGANG-BEREINIGUNG")
    print("=" * 80)
    print("Datenbank:", DB)

    if not DB.exists():
        raise RuntimeError("Datenbank fehlt: " + str(DB))

    con = duckdb.connect(str(DB), read_only=True)

    try:
        rows = con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()

        names = [r[0] for r in rows]

        old_language = [
            "app_languages",
            "staff_language_profiles",
            "case_language_profiles",
            "communication_language_rules",
            "language_profile_audit"
        ]

        print("Tabellenzahl:", len(names))
        print("")

        print("ALTSPRACHEN-OBJEKTE")
        print("-" * 80)
        for table in old_language:
            print(table + ":", "NOCH VORHANDEN" if table in names else "entfernt")

        print("")
        print("SPRACHKONTEXT V2")
        print("-" * 80)
        lang_tables = [x for x in names if x.startswith("lang_")]
        for table in lang_tables:
            try:
                count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                print(table + ":", count)
            except Exception as exc:
                print(table + ": nicht lesbar:", repr(exc))

        if "lang_language_catalog" in names:
            eu24 = con.execute("""
                SELECT COUNT(*)
                FROM lang_language_catalog
                WHERE eu_official = TRUE
            """).fetchone()[0]
            print("EU24:", eu24)
            if eu24 != 24:
                raise RuntimeError("EU24-Sprachkatalog ist nicht vollständig: " + str(eu24))

        print("")
        print("POSTEINGANG-TABELLEN")
        print("-" * 80)
        post_tables = [x for x in names if x.startswith("posteingang_")]
        for table in post_tables:
            try:
                count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                print(table + ":", count)
            except Exception as exc:
                print(table + ": nicht lesbar:", repr(exc))

        print("")
        print("SCHWEDEN-ARBEITSRECHT-VORLAGE")
        print("-" * 80)

        if "lang_case_language_settings" in names:
            row = con.execute("""
                SELECT
                    case_template_key,
                    jurisdiction_country_code,
                    country_language_code,
                    procedural_language_code,
                    internal_work_language_code,
                    default_document_language_code
                FROM lang_case_language_settings
                WHERE case_template_key = 'TEMPLATE_SE_ARBEITSRECHT'
            """).fetchone()
            print(row)
        else:
            print("lang_case_language_settings fehlt.")

        if "lang_participant_language_settings" in names:
            rows = con.execute("""
                SELECT
                    participant_profile_key,
                    participant_role,
                    communication_language_code,
                    document_language_code,
                    actual_or_spoken_language_code,
                    created_after_mandate_acceptance,
                    accepted_client_required
                FROM lang_participant_language_settings
                ORDER BY participant_profile_key
            """).fetchall()

            print("")
            print("BETEILIGTEN-SPRACHPROFILE")
            print("-" * 80)
            for r in rows:
                print(r)

    finally:
        con.close()

    print("")
    print("DATENBANKPRUEFUNG OK")

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
