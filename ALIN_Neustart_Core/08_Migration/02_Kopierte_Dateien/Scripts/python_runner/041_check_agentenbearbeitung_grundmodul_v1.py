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
        "agent_task_catalog",
        "agent_case_scope",
        "agent_work_queue",
        "agent_processing_audit",
    ]

    for t in required:
        print(t + ":", "OK" if t in tables else "FEHLT")
        if t not in tables:
            raise RuntimeError("Tabelle fehlt: " + t)

    task_count = con.execute("SELECT COUNT(*) FROM agent_task_catalog WHERE active = TRUE").fetchone()[0]
    job_count = con.execute("SELECT COUNT(*) FROM agent_work_queue").fetchone()[0]

    scope = con.execute("""
        SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
               internal_work_language_code
        FROM agent_case_scope
        WHERE case_template_key = 'TEMPLATE_SE_ARBEITSRECHT'
    """).fetchone()

    print("Aufgaben:", task_count)
    print("Jobs:", job_count)
    print("Schweden-Kontext:", scope)

    if task_count < 5:
        raise RuntimeError("Aufgabenkatalog unvollständig.")

    if tuple(scope or ()) != ("SE", "sv", "sv", "de"):
        raise RuntimeError("Schweden-Kontext fehlerhaft: " + repr(scope))

finally:
    con.close()
