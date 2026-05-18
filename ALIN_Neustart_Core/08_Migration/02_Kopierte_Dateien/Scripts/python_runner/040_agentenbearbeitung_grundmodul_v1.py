# -*- coding: utf-8 -*-
import sys
import json
import uuid
import hashlib
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
LOG = ROOT / "Windows_App" / "Logs"
OUT = LOG / "Agentenbearbeitung"
CONFIG = ROOT / "Config" / "agentenbearbeitung_grundmodul_v1.json"

OUT.mkdir(parents=True, exist_ok=True)

CONFIG_DATA = {
    "version": "V1",
    "module": "Agentenbearbeitung Grundmodul",
    "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
    "case_context": {
        "matter_type": "Schwedischer Arbeitsrechtsstreit",
        "parties_context": "Arbeitnehmer gegen kommunalen Arbeitgeber",
        "jurisdiction_country_code": "SE",
        "official_language_code": "sv",
        "procedural_language_code": "sv",
        "internal_work_language_code": "de"
    },
    "principle": "Die Agentenbearbeitung bereitet Aktenstruktur und fachliche Sichtung vor. Die abschließende anwaltliche Bewertung bleibt gesperrt.",
    "tasks": [
        {
            "task_key": "DOKUMENTART_ERKENNEN",
            "task_order": 10,
            "task_label": "Dokumentart erkennen",
            "task_scope": "Formale Art des Dokuments bestimmen, etwa Schriftsatz, Nachweis, Aussage, E-Mail, Bescheid, Protokoll, Bild oder Kontextmaterial.",
            "allowed_output": "Vorschlag zur Dokumentart mit Begründung und Unsicherheitsgrad.",
            "forbidden_output": "Keine rechtliche Verwertung und keine abschließende Beweiseinordnung."
        },
        {
            "task_key": "SPRACHE_UND_UEBERSETZUNG_PRUEFEN",
            "task_order": 20,
            "task_label": "Sprache und Arbeitsübersetzung prüfen",
            "task_scope": "Erkannte Sprache, Mehrsprachigkeit und grobe deutsche Arbeitsübersetzung prüfen.",
            "allowed_output": "Sprachprofil, Übersetzungsbedarf und Hinweis auf unklare Textstellen.",
            "forbidden_output": "Keine verbindliche beglaubigte Übersetzung."
        },
        {
            "task_key": "SACHVERHALTSBEZUG_VORBEREITEN",
            "task_order": 30,
            "task_label": "Sachverhaltsbezug vorbereiten",
            "task_scope": "Zeit, Beteiligte, Vorgang und mögliche Zuordnung zu einem Sachverhaltsabschnitt vorbereiten.",
            "allowed_output": "Strukturvorschlag für die spätere Akte.",
            "forbidden_output": "Keine endgültige Aktenzuordnung."
        },
        {
            "task_key": "BEWEIS_ODER_ENTLASTUNG_VORSCHLAG",
            "task_order": 40,
            "task_label": "Beweis- oder Entlastungsvorschlag vorbereiten",
            "task_scope": "Nur als Vorschlag kennzeichnen, ob ein Dokument als Nachweis, Aussage, Entlastung, Belastung oder Kontextmaterial in Betracht kommt.",
            "allowed_output": "Nicht bindender Vorschlag mit Fundstellenhinweis.",
            "forbidden_output": "Keine Beweiswürdigung, keine rechtliche Endbewertung."
        },
        {
            "task_key": "ANWALTVORLAGE_STRUKTURIEREN",
            "task_order": 50,
            "task_label": "Anwaltvorlage strukturieren",
            "task_scope": "Kurzblatt für den Anwalt vorbereiten: Dokument, Sprache, Beteiligte, mögliche Bedeutung, offene Prüfpunkte.",
            "allowed_output": "Strukturierte Vorlage zur anwaltlichen Entscheidung.",
            "forbidden_output": "Keine Klageentscheidung und keine Freigabe nach außen."
        }
    ]
}

DDL = [
    """
    CREATE TABLE IF NOT EXISTS agent_task_catalog (
        task_key VARCHAR,
        task_order INTEGER,
        task_label VARCHAR,
        task_scope VARCHAR,
        allowed_output VARCHAR,
        forbidden_output VARCHAR,
        active BOOLEAN,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_case_scope (
        scope_key VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        case_template_key VARCHAR,
        jurisdiction_country_code VARCHAR,
        official_language_code VARCHAR,
        procedural_language_code VARCHAR,
        internal_work_language_code VARCHAR,
        matter_type VARCHAR,
        parties_context VARCHAR,
        scope_notes VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_work_queue (
        agent_job_id VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        review_id VARCHAR,
        intake_id VARCHAR,
        case_template_key VARCHAR,
        source_path VARCHAR,
        original_name VARCHAR,
        document_language_code VARCHAR,
        rough_translation_target_language_code VARCHAR,
        task_key VARCHAR,
        task_order INTEGER,
        job_status VARCHAR,
        priority INTEGER,
        allowed_scope VARCHAR,
        forbidden_scope VARCHAR,
        expected_output_json VARCHAR,
        result_json VARCHAR,
        notes VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_processing_audit (
        audit_id VARCHAR,
        audit_time TIMESTAMP,
        audit_area VARCHAR,
        audit_status VARCHAR,
        intake_id VARCHAR,
        task_key VARCHAR,
        details VARCHAR
    )
    """
]

REQUIRED_COLUMNS = {
    "agent_task_catalog": [
        ("task_key", "VARCHAR"),
        ("task_order", "INTEGER"),
        ("task_label", "VARCHAR"),
        ("task_scope", "VARCHAR"),
        ("allowed_output", "VARCHAR"),
        ("forbidden_output", "VARCHAR"),
        ("active", "BOOLEAN"),
        ("updated_at", "TIMESTAMP"),
    ],
    "agent_case_scope": [
        ("scope_key", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("case_template_key", "VARCHAR"),
        ("jurisdiction_country_code", "VARCHAR"),
        ("official_language_code", "VARCHAR"),
        ("procedural_language_code", "VARCHAR"),
        ("internal_work_language_code", "VARCHAR"),
        ("matter_type", "VARCHAR"),
        ("parties_context", "VARCHAR"),
        ("scope_notes", "VARCHAR"),
    ],
    "agent_work_queue": [
        ("agent_job_id", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("review_id", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("case_template_key", "VARCHAR"),
        ("source_path", "VARCHAR"),
        ("original_name", "VARCHAR"),
        ("document_language_code", "VARCHAR"),
        ("rough_translation_target_language_code", "VARCHAR"),
        ("task_key", "VARCHAR"),
        ("task_order", "INTEGER"),
        ("job_status", "VARCHAR"),
        ("priority", "INTEGER"),
        ("allowed_scope", "VARCHAR"),
        ("forbidden_scope", "VARCHAR"),
        ("expected_output_json", "VARCHAR"),
        ("result_json", "VARCHAR"),
        ("notes", "VARCHAR"),
    ],
    "agent_processing_audit": [
        ("audit_id", "VARCHAR"),
        ("audit_time", "TIMESTAMP"),
        ("audit_area", "VARCHAR"),
        ("audit_status", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("task_key", "VARCHAR"),
        ("details", "VARCHAR"),
    ],
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def q(name):
    return '"' + str(name).replace('"', '""') + '"'

def existing_columns(con, table):
    try:
        rows = con.execute("PRAGMA table_info(" + q(table) + ")").fetchall()
        return {str(r[1]).lower() for r in rows}
    except Exception:
        return set()

def ensure_schema(con):
    for ddl in DDL:
        con.execute(ddl)

    for table, cols in REQUIRED_COLUMNS.items():
        have = existing_columns(con, table)
        for col, dtype in cols:
            if col.lower() not in have:
                con.execute("ALTER TABLE " + q(table) + " ADD COLUMN " + q(col) + " " + dtype)

def audit(con, status, intake_id, task_key, details):
    con.execute(
        """
        INSERT INTO agent_processing_audit
        (audit_id, audit_time, audit_area, audit_status, intake_id, task_key, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            "agentenbearbeitung_grundmodul_v1",
            status,
            intake_id,
            task_key,
            details
        ]
    )

def seed_task_catalog(con):
    task_keys = [x["task_key"] for x in CONFIG_DATA["tasks"]]

    if task_keys:
        con.execute(
            "DELETE FROM agent_task_catalog WHERE task_key IN (" + ",".join(["?"] * len(task_keys)) + ")",
            task_keys
        )

    for t in CONFIG_DATA["tasks"]:
        con.execute(
            """
            INSERT INTO agent_task_catalog
            (task_key, task_order, task_label, task_scope, allowed_output, forbidden_output, active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP)
            """,
            [
                t["task_key"],
                int(t["task_order"]),
                t["task_label"],
                t["task_scope"],
                t["allowed_output"],
                t["forbidden_output"],
            ]
        )

def seed_case_scope(con):
    c = CONFIG_DATA["case_context"]
    scope_key = CONFIG_DATA["case_template_key"] + "_AGENT_SCOPE"

    con.execute("DELETE FROM agent_case_scope WHERE scope_key = ?", [scope_key])

    con.execute(
        """
        INSERT INTO agent_case_scope
        (scope_key, created_at, updated_at, case_template_key, jurisdiction_country_code,
         official_language_code, procedural_language_code, internal_work_language_code,
         matter_type, parties_context, scope_notes)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            scope_key,
            CONFIG_DATA["case_template_key"],
            c["jurisdiction_country_code"],
            c["official_language_code"],
            c["procedural_language_code"],
            c["internal_work_language_code"],
            c["matter_type"],
            c["parties_context"],
            CONFIG_DATA["principle"]
        ]
    )

def read_review_queue(con):
    tables = [x[0] for x in con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()]

    if "anwalt_review_queue" not in tables:
        return []

    rows = con.execute("""
        SELECT review_id, intake_id, case_template_key, source_path, original_name,
               document_language_code, rough_translation_target_language_code,
               lawyer_review_status, next_required_action
        FROM anwalt_review_queue
        ORDER BY created_at, original_name
    """).fetchall()

    result = []
    for r in rows:
        result.append({
            "review_id": r[0] or "",
            "intake_id": r[1] or "",
            "case_template_key": r[2] or CONFIG_DATA["case_template_key"],
            "source_path": r[3] or "",
            "original_name": r[4] or "",
            "document_language_code": r[5] or "unknown",
            "rough_translation_target_language_code": r[6] or "de",
            "lawyer_review_status": r[7] or "",
            "next_required_action": r[8] or "",
        })

    return result

def job_id(review_id, intake_id, task_key, source_path):
    base = "|".join([review_id, intake_id, task_key, source_path])
    return "AGENTJOB_" + hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:20]

def expected_output(task_key):
    return {
        "task_key": task_key,
        "status": "offen",
        "output_must_be_marked_as": "Vorschlag, nicht abschließende anwaltliche Bewertung",
        "required_fields": [
            "kurzbefund",
            "begruendung",
            "unsicherheiten",
            "fundstellen_hinweise",
            "anwalt_pruefpunkte"
        ]
    }

def build_agent_jobs(con):
    review_rows = read_review_queue(con)
    tasks = CONFIG_DATA["tasks"]

    jobs = []

    for rr in review_rows:
        for t in tasks:
            jid = job_id(rr["review_id"], rr["intake_id"], t["task_key"], rr["source_path"])

            priority = 50
            if rr["document_language_code"] in ("unknown", "", None):
                priority = 20
            if t["task_key"] == "SPRACHE_UND_UEBERSETZUNG_PRUEFEN":
                priority = min(priority, 10)

            jobs.append({
                "agent_job_id": jid,
                "review_id": rr["review_id"],
                "intake_id": rr["intake_id"],
                "case_template_key": rr["case_template_key"],
                "source_path": rr["source_path"],
                "original_name": rr["original_name"],
                "document_language_code": rr["document_language_code"],
                "rough_translation_target_language_code": rr["rough_translation_target_language_code"],
                "task_key": t["task_key"],
                "task_order": int(t["task_order"]),
                "job_status": "OFFEN",
                "priority": int(priority),
                "allowed_scope": t["allowed_output"],
                "forbidden_scope": t["forbidden_output"],
                "expected_output_json": json.dumps(expected_output(t["task_key"]), ensure_ascii=False),
                "result_json": "",
                "notes": "Aus Anwaltvorlage erzeugte Agentenaufgabe. Keine abschließende rechtliche Entscheidung."
            })

    return jobs

def upsert_jobs(con, jobs):
    for j in jobs:
        con.execute(
            """
            DELETE FROM agent_work_queue
            WHERE agent_job_id = ?
            """,
            [j["agent_job_id"]]
        )

        con.execute(
            """
            INSERT INTO agent_work_queue
            (agent_job_id, created_at, updated_at, review_id, intake_id, case_template_key,
             source_path, original_name, document_language_code, rough_translation_target_language_code,
             task_key, task_order, job_status, priority, allowed_scope, forbidden_scope,
             expected_output_json, result_json, notes)
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                j["agent_job_id"],
                j["review_id"],
                j["intake_id"],
                j["case_template_key"],
                j["source_path"],
                j["original_name"],
                j["document_language_code"],
                j["rough_translation_target_language_code"],
                j["task_key"],
                j["task_order"],
                j["job_status"],
                j["priority"],
                j["allowed_scope"],
                j["forbidden_scope"],
                j["expected_output_json"],
                j["result_json"],
                j["notes"],
            ]
        )

def write_reports(jobs):
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)

    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"AGENTENBEARBEITUNG_GRUNDMODUL_V1_{ts}.txt"
    csv_file = OUT / f"AGENTENBEARBEITUNG_GRUNDMODUL_V1_{ts}.csv"
    json_file = OUT / f"AGENTENBEARBEITUNG_GRUNDMODUL_V1_{ts}.json"

    data = {
        "time": now(),
        "case_template_key": CONFIG_DATA["case_template_key"],
        "jobs_count": len(jobs),
        "jobs": jobs,
        "principle": CONFIG_DATA["principle"],
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "agent_job_id",
        "review_id",
        "intake_id",
        "case_template_key",
        "original_name",
        "source_path",
        "document_language_code",
        "rough_translation_target_language_code",
        "task_key",
        "task_order",
        "job_status",
        "priority",
        "allowed_scope",
        "forbidden_scope",
        "notes",
    ]

    import csv
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for j in jobs:
            writer.writerow({k: j.get(k, "") for k in fields})

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("AGENTENBEARBEITUNG GRUNDMODUL V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Fallvorlage: " + CONFIG_DATA["case_template_key"] + "\n")
        f.write("Agentenaufgaben: " + str(len(jobs)) + "\n\n")

        f.write("LEITLINIE\n")
        f.write("-" * 80 + "\n")
        f.write(CONFIG_DATA["principle"] + "\n\n")

        f.write("AUFGABENKATALOG\n")
        f.write("-" * 80 + "\n")
        for t in CONFIG_DATA["tasks"]:
            f.write(str(t["task_order"]) + " | " + t["task_key"] + " | " + t["task_label"] + "\n")
            f.write("Erlaubt: " + t["allowed_output"] + "\n")
            f.write("Verboten: " + t["forbidden_output"] + "\n\n")

        f.write("OFFENE AUFGABEN\n")
        f.write("-" * 80 + "\n")
        if not jobs:
            f.write("Keine Anwaltvorlagen gefunden. Keine Agentenaufgaben erzeugt.\n")
        else:
            for i, j in enumerate(jobs, start=1):
                f.write("\n" + str(i) + ". " + j["task_key"] + "\n")
                f.write("Dokument: " + j["original_name"] + "\n")
                f.write("Intake-ID: " + j["intake_id"] + "\n")
                f.write("Sprache: " + j["document_language_code"] + "\n")
                f.write("Priorität: " + str(j["priority"]) + "\n")
                f.write("Quelle: " + j["source_path"] + "\n")

    return txt, csv_file, json_file

def verify(con):
    task_count = con.execute("SELECT COUNT(*) FROM agent_task_catalog WHERE active = TRUE").fetchone()[0]
    scope = con.execute("""
        SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
               internal_work_language_code
        FROM agent_case_scope
        WHERE case_template_key = 'TEMPLATE_SE_ARBEITSRECHT'
    """).fetchone()
    job_count = con.execute("SELECT COUNT(*) FROM agent_work_queue").fetchone()[0]

    if task_count < 5:
        raise RuntimeError("Aufgabenkatalog unvollständig: " + str(task_count))

    if tuple(scope or ()) != ("SE", "sv", "sv", "de"):
        raise RuntimeError("Agenten-Fallkontext Schweden Arbeitsrecht fehlerhaft: " + repr(scope))

    return {
        "task_count": task_count,
        "scope": tuple(scope),
        "job_count": job_count
    }

def main():
    con = duckdb.connect(str(DB))
    try:
        ensure_schema(con)
        seed_task_catalog(con)
        seed_case_scope(con)
        jobs = build_agent_jobs(con)
        upsert_jobs(con, jobs)
        result = verify(con)
        audit(con, "OK", "", "", json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        try:
            audit(con, "FEHLER", "", "", repr(exc))
        except Exception:
            pass
        raise
    finally:
        con.close()

    txt, csv_file, json_file = write_reports(jobs)

    print("")
    print("AGENTENBEARBEITUNG_GRUNDMODUL_V1 FERTIG")
    print("Fallvorlage:", CONFIG_DATA["case_template_key"])
    print("Agentenaufgaben:", len(jobs))
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", json_file)
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
