# -*- coding: utf-8 -*-
import sys
import csv
import json
import datetime
from pathlib import Path

import duckdb

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"

OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "Windows_App" / "Logs" / "DB_CLEANUP_POSTEINGANG"
OUTDIR.mkdir(parents=True, exist_ok=True)

OLD_LANGUAGE_TABLES = [
    "app_languages",
    "staff_language_profiles",
    "case_language_profiles",
    "communication_language_rules",
    "language_profile_audit"
]

SAFE_DELETE_PREFIXES = [
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

TEXT_TYPES = [
    "CHAR",
    "VARCHAR",
    "TEXT",
    "STRING",
    "JSON"
]

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def table_exists(con, table):
    row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table]
    ).fetchone()
    return row and row[0] > 0

def all_tables(con):
    rows = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    ).fetchall()
    return [r[0] for r in rows]

def text_columns(con, table):
    rows = con.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'main'
          AND table_name = ?
        ORDER BY ordinal_position
        """,
        [table]
    ).fetchall()

    cols = []
    for col, dtype in rows:
        dt = str(dtype).upper()
        if any(x in dt for x in TEXT_TYPES):
            cols.append(col)
    return cols

def build_where(cols):
    parts = []
    params = []
    for col in cols:
        for pattern in PATTERNS:
            parts.append("CAST(" + q(col) + " AS VARCHAR) ILIKE ?")
            params.append(pattern)
    if not parts:
        return "", []
    return "(" + " OR ".join(parts) + ")", params

def export_rows(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if v is None else str(v) for v in row])

def safe_delete_table(table):
    if table in SAFE_EXCLUDE_TABLES:
        return False
    return any(table.startswith(prefix) for prefix in SAFE_DELETE_PREFIXES)

def insert_setup_audit(con, status, details):
    try:
        if table_exists(con, "setup_audit"):
            con.execute(
                """
                INSERT INTO setup_audit
                (timestamp, module, action, status)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
                """,
                [
                    "POSTEINGANG_CLEANUP",
                    details[:1000],
                    status
                ]
            )
    except Exception:
        pass

def main():
    con = duckdb.connect(str(DB))

    result = {
        "time": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "database": str(DB),
        "outdir": str(OUTDIR),
        "dropped_old_tables": [],
        "deleted_rows": [],
        "reported_only": []
    }

    try:
        for table in OLD_LANGUAGE_TABLES:
            if table_exists(con, table):
                con.execute("DROP TABLE " + q(table))
                result["dropped_old_tables"].append(table)

        for table in all_tables(con):
            cols = text_columns(con, table)
            if not cols:
                continue

            where, params = build_where(cols)
            if not where:
                continue

            sql_count = "SELECT COUNT(*) FROM " + q(table) + " WHERE " + where
            count = con.execute(sql_count, params).fetchone()[0]

            if count == 0:
                continue

            sql_select = "SELECT * FROM " + q(table) + " WHERE " + where
            cur = con.execute(sql_select, params)
            rows = cur.fetchall()
            columns = [d[0] for d in cur.description]

            export_path = OUTDIR / (table + "_matched_rows.csv")
            export_rows(export_path, columns, rows)

            if safe_delete_table(table):
                sql_delete = "DELETE FROM " + q(table) + " WHERE " + where
                con.execute(sql_delete, params)
                result["deleted_rows"].append({
                    "table": table,
                    "rows": count,
                    "backup_csv": str(export_path)
                })
            else:
                result["reported_only"].append({
                    "table": table,
                    "rows": count,
                    "backup_csv": str(export_path),
                    "note": "Nicht automatisch gelöscht, weil keine sichere Posteingangs-Lauftabelle."
                })

        insert_setup_audit(
            con,
            "OK",
            "Posteingang DB-Bereinigung: " + json.dumps(result, ensure_ascii=False)
        )

        result_path = OUTDIR / "POSTEINGANG_DB_CLEANUP_RESULT.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

        print("")
        print("POSTEINGANG_DB_CLEANUP FERTIG")
        print("Gelöschte alte Sprachtabellen:", result["dropped_old_tables"])
        print("Bereinigte Tabellen:", result["deleted_rows"])
        print("Nur berichtet:", result["reported_only"])
        print("Ergebnis:", result_path)

    except Exception as exc:
        insert_setup_audit(con, "FEHLER", repr(exc))
        raise

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
