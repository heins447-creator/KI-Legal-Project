# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import duckdb

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"

OLD_LANGUAGE_TABLES = [
    "app_languages",
    "staff_language_profiles",
    "case_language_profiles",
    "communication_language_rules",
    "language_profile_audit"
]

SAFE_TABLE_PREFIXES = [
    "posteingang_"
]

SAFE_EXCLUDE_TABLES = {
    "posteingang_allowed_research_sources"
}

PATTERNS = [
    "%TEST_%",
    "%TESTLANG%",
    "%Testdatei%",
    "%Arbeitsvertrag_ungefaehrlich%",
    "%aktive_Datei%",
    "%signierte_mail%",
    "%SICHERHEITSGATE_V2%",
    "%SPRACHKONTEXT_GATE_V2%",
    "%ARBEITSSTRUKTUR_V1%",
    "%POSTEINGANG_ARBEITSSTRUKTUR_V1%",
    "%POSTEINGANG_SICHERHEITSGATE_V2%",
    "%POSTEINGANG_SPRACHKONTEXT_GATE_V2%",
    "%_entscheidungskarte.json%",
    "%_sicherheitskarte.json%",
    "%_sicherheitsbericht.json%",
    "%_sprachkarte.json%",
    "%_sprachbericht.json%",
    "%20260510162657%",
    "%202605101636%",
    "%20260510172132%"
]

TEXT_TYPES = ["CHAR", "VARCHAR", "TEXT", "STRING", "JSON"]

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def table_exists(con, table):
    return con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table]
    ).fetchone()[0] > 0

def text_columns(con, table):
    rows = con.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table]
    ).fetchall()

    out = []
    for col, dtype in rows:
        if any(t in str(dtype).upper() for t in TEXT_TYPES):
            out.append(col)
    return out

def build_where(cols):
    parts = []
    params = []
    for col in cols:
        for pat in PATTERNS:
            parts.append("CAST(" + q(col) + " AS VARCHAR) ILIKE ?")
            params.append(pat)
    if not parts:
        return "", []
    return "(" + " OR ".join(parts) + ")", params

def safe_table(table):
    if table in SAFE_EXCLUDE_TABLES:
        return False
    return any(table.startswith(prefix) for prefix in SAFE_TABLE_PREFIXES)

def main():
    con = duckdb.connect(str(DB), read_only=True)

    try:
        old_found = [t for t in OLD_LANGUAGE_TABLES if table_exists(con, t)]
        if old_found:
            raise RuntimeError("Alte Sprachtabellen noch vorhanden: " + repr(old_found))

        tables = con.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        ).fetchall()

        remaining = []

        for row in tables:
            table = row[0]
            if not safe_table(table):
                continue

            cols = text_columns(con, table)
            where, params = build_where(cols)
            if not where:
                continue

            count = con.execute(
                "SELECT COUNT(*) FROM " + q(table) + " WHERE " + where,
                params
            ).fetchone()[0]

            if count:
                remaining.append((table, count))

        if remaining:
            raise RuntimeError("Test-/Altlastenreste in Posteingangstabellen: " + repr(remaining))

        print("")
        print("POSTEINGANG_CLEAN_VERIFY OK")
        print("Alte Sprachtabellen: entfernt")
        print("Posteingangstabellen: keine Test-/Altlastenreste gefunden")

    finally:
        con.close()

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
