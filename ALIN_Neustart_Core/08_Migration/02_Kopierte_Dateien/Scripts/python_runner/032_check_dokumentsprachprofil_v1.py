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
    con = duckdb.connect(str(DB), read_only=True)
    try:
        tables = [
            x[0] for x in con.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                ORDER BY table_name
            """).fetchall()
        ]

        required = [
            "posteingang_document_language_profile",
            "posteingang_document_language_audit",
        ]

        for table in required:
            if table not in tables:
                raise RuntimeError("Pflichttabelle fehlt: " + table)

        profile_count = con.execute(
            "SELECT COUNT(*) FROM posteingang_document_language_profile"
        ).fetchone()[0]

        multilingual_count = con.execute(
            "SELECT COUNT(*) FROM posteingang_document_language_profile WHERE is_multilingual = TRUE"
        ).fetchone()[0]

        rough_translation_count = con.execute(
            "SELECT COUNT(*) FROM posteingang_document_language_profile WHERE rough_translation_required = TRUE"
        ).fetchone()[0]

        audit_count = con.execute(
            "SELECT COUNT(*) FROM posteingang_document_language_audit"
        ).fetchone()[0]

        print("DOKUMENTSPRACHPROFIL DIREKTPRUEFUNG OK")
        print("Profile:", profile_count)
        print("Mehrsprachig:", multilingual_count)
        print("Deutsch-Übersetzung erforderlich:", rough_translation_count)
        print("Audit:", audit_count)
    finally:
        con.close()

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
