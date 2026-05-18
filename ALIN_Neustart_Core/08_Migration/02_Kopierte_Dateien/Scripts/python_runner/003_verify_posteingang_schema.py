import sys
import os
import duckdb
import traceback

db_path = sys.argv[1]
report_path = sys.argv[2]

def w(text=""):
    with open(report_path, "a", encoding="utf-8", newline="\n") as f:
        f.write(str(text) + "\n")

required = [
    "posteingang_intake",
    "posteingang_checks",
    "posteingang_decisions",
    "posteingang_events",
    "posteingang_allowed_research_sources",
]

try:
    w("")
    w("PYTHON SCHEMA-PRUEFUNG START")
    con = duckdb.connect(db_path, read_only=True)

    rows = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name LIKE 'posteingang_%'
        ORDER BY table_name
    """).fetchall()

    found = [r[0] for r in rows]

    w("Gefundene Posteingangstabellen:")
    for name in found:
        count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        w(f"- {name}: {count} Zeilen")

    missing = [name for name in required if name not in found]

    if missing:
        w("FEHLENDE TABELLEN:")
        for name in missing:
            w("- " + name)
        sys.exit(2)

    con.close()
    w("PYTHON SCHEMA-PRUEFUNG OK")
    sys.exit(0)

except Exception:
    w("PYTHON SCHEMA-PRUEFUNG FEHLER")
    w(traceback.format_exc())
    sys.exit(1)
