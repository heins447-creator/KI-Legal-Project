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
        "agent_fact_context_suggestion",
        "agent_fact_context_audit",
    ]

    for t in required:
        print(t + ":", "OK" if t in tables else "FEHLT")
        if t not in tables:
            raise RuntimeError("Tabelle fehlt: " + t)

    suggestions = con.execute("SELECT COUNT(*) FROM agent_fact_context_suggestion").fetchone()[0]
    audits = con.execute("SELECT COUNT(*) FROM agent_fact_context_audit").fetchone()[0]

    print("Sachverhaltsvorschläge:", suggestions)
    print("Audit:", audits)

    if "agent_work_queue" in tables:
        done = con.execute("""
            SELECT COUNT(*)
            FROM agent_work_queue
            WHERE task_key = 'SACHVERHALTSBEZUG_VORBEREITEN'
              AND job_status IN ('SACHVERHALTSBEZUG_VORGESCHLAGEN', 'QUELLDATEI_FEHLT')
        """).fetchone()[0]

        total = con.execute("""
            SELECT COUNT(*)
            FROM agent_work_queue
            WHERE task_key = 'SACHVERHALTSBEZUG_VORBEREITEN'
        """).fetchone()[0]

        print("Agentenaufgaben Sachverhaltsbezug:", done, "von", total)

finally:
    con.close()
