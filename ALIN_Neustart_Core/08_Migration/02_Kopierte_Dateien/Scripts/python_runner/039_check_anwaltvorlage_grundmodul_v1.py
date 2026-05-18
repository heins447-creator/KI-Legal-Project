# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import duckdb

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

db = Path(r"I:\KI_Legal_Project\Database\Legal_Brain.duckdb")
con = duckdb.connect(str(db), read_only=True)

try:
    tables = [x[0] for x in con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()]

    required = [
        "anwalt_review_queue",
        "anwalt_review_audit",
        "anwalt_case_context_template",
    ]

    for t in required:
        print(t + ":", "OK" if t in tables else "FEHLT")
        if t not in tables:
            raise RuntimeError("Tabelle fehlt: " + t)

    print("Queue:", con.execute("SELECT COUNT(*) FROM anwalt_review_queue").fetchone()[0])

    row = con.execute("""
        SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
               internal_work_language_code, rough_translation_target_language_code
        FROM anwalt_case_context_template
        WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
    """).fetchone()

    print("Schweden-Kontext:", row)

    if tuple(row or ()) != ("SE", "sv", "sv", "de", "de"):
        raise RuntimeError("Schweden-Kontext fehlerhaft: " + repr(row))

finally:
    con.close()
