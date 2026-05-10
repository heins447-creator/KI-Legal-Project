# -*- coding: utf-8 -*-
import sys
import json
import csv
import uuid
import re
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
OUT = LOG / "Agent_Sachverhaltsbezug"
CONFIG = ROOT / "Config" / "agent_sachverhaltsbezug_v1.json"

OUT.mkdir(parents=True, exist_ok=True)

CONFIG_DATA = {
    "version": "V1",
    "agent": "SACHVERHALTSBEZUG_VORBEREITEN",
    "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
    "case_context": {
        "case_type": "Schwedischer Arbeitsrechtsstreit",
        "parties": "Arbeitnehmer gegen kommunalen Arbeitgeber",
        "official_language_code": "sv",
        "procedural_language_code": "sv",
        "internal_work_language_code": "de"
    },
    "principle": "Der Agent bereitet nur einen moeglichen Sachverhaltsbezug vor. Er trifft keine rechtliche Bewertung und keine Beweiswuerdigung.",
    "allowed_contexts": [
        "ANSTELLUNG_VERTRAG",
        "UNTERRICHT_SCHULORGANISATION",
        "WARNUNG_MASSNAHME",
        "KUENDIGUNG_AUSSCHLUSS",
        "ARBEITSMILJOE_ARBEITSUMFELD",
        "ELTERN_SCHUELER_KOMMUNIKATION",
        "BEHOERDE_GERICHT_VERFAHREN",
        "ZEITLICHER_ABLAUF",
        "SONSTIGES_UNKLAR"
    ],
    "forbidden_conclusions": [
        "Beweiswert",
        "Entlastungswert",
        "rechtliche Relevanz",
        "prozessuale Verwertbarkeit",
        "Verschulden",
        "Glaubwuerdigkeit",
        "endgueltige Aktenzuordnung",
        "Klageentscheidung"
    ]
}

DDL = [
    """
    CREATE TABLE IF NOT EXISTS agent_fact_context_suggestion (
        fact_context_id VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        agent_job_id VARCHAR,
        review_id VARCHAR,
        intake_id VARCHAR,
        case_template_key VARCHAR,
        source_path VARCHAR,
        original_name VARCHAR,
        source_document_type VARCHAR,
        source_document_language_code VARCHAR,
        suggested_context_key VARCHAR,
        suggested_context_label VARCHAR,
        confidence VARCHAR,
        timeline_hint_date VARCHAR,
        participant_hints_json VARCHAR,
        reason_terms_json VARCHAR,
        text_extract VARCHAR,
        allowed_next_agent_tasks_json VARCHAR,
        forbidden_conclusions_json VARCHAR,
        status VARCHAR,
        notes VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_fact_context_audit (
        audit_id VARCHAR,
        audit_time TIMESTAMP,
        audit_area VARCHAR,
        audit_status VARCHAR,
        agent_job_id VARCHAR,
        intake_id VARCHAR,
        details VARCHAR
    )
    """
]

REQUIRED_COLUMNS = {
    "agent_fact_context_suggestion": [
        ("fact_context_id", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("agent_job_id", "VARCHAR"),
        ("review_id", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("case_template_key", "VARCHAR"),
        ("source_path", "VARCHAR"),
        ("original_name", "VARCHAR"),
        ("source_document_type", "VARCHAR"),
        ("source_document_language_code", "VARCHAR"),
        ("suggested_context_key", "VARCHAR"),
        ("suggested_context_label", "VARCHAR"),
        ("confidence", "VARCHAR"),
        ("timeline_hint_date", "VARCHAR"),
        ("participant_hints_json", "VARCHAR"),
        ("reason_terms_json", "VARCHAR"),
        ("text_extract", "VARCHAR"),
        ("allowed_next_agent_tasks_json", "VARCHAR"),
        ("forbidden_conclusions_json", "VARCHAR"),
        ("status", "VARCHAR"),
        ("notes", "VARCHAR"),
    ],
    "agent_fact_context_audit": [
        ("audit_id", "VARCHAR"),
        ("audit_time", "TIMESTAMP"),
        ("audit_area", "VARCHAR"),
        ("audit_status", "VARCHAR"),
        ("agent_job_id", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("details", "VARCHAR"),
    ],
}

TEXT_EXTENSIONS = {".txt", ".csv", ".json", ".xml", ".md", ".eml", ".html", ".htm"}

CONTEXT_RULES = [
    {
        "key": "ANSTELLUNG_VERTRAG",
        "label": "Anstellung, Vertrag oder Beschäftigungsgrundlage",
        "terms": [
            "arbeitsvertrag", "arbetsavtal", "anställning", "anstallning", "employment",
            "vertrag", "beschäftigung", "beschaeftigung", "anställningsavtal"
        ]
    },
    {
        "key": "UNTERRICHT_SCHULORGANISATION",
        "label": "Unterricht, Schulorganisation oder pädagogischer Ablauf",
        "terms": [
            "unterricht", "lektion", "klass", "klasse", "skola", "schule", "elev",
            "schüler", "schueler", "lärare", "larare", "lehrer", "schema", "stundenplan",
            "bücher", "buecher", "läromedel", "laromedel"
        ]
    },
    {
        "key": "WARNUNG_MASSNAHME",
        "label": "Warnung, Maßnahme oder dienstliche Reaktion",
        "terms": [
            "varning", "warning", "abmahnung", "verwarnung", "maßnahme", "massnahme",
            "möte", "mote", "gespräch", "gespraech", "disciplin", "konsekvens"
        ]
    },
    {
        "key": "KUENDIGUNG_AUSSCHLUSS",
        "label": "Kündigung, Ausschluß, Hausverbot oder Beendigung",
        "terms": [
            "kündigung", "kuendigung", "uppsägning", "uppsagning", "avsked", "termination",
            "hausverbot", "avstängning", "avstangning", "lockout", "beendigung"
        ]
    },
    {
        "key": "ARBEITSMILJOE_ARBEITSUMFELD",
        "label": "Arbeitsumfeld, Arbeitsmiljö oder organisatorische Belastung",
        "terms": [
            "arbetsmiljö", "arbetsmiljo", "arbeitsmilieu", "arbeitsumfeld",
            "belastung", "stress", "budget", "personal", "personaleinkauf",
            "kränkning", "krankning", "mobbing", "diskriminierung"
        ]
    },
    {
        "key": "ELTERN_SCHUELER_KOMMUNIKATION",
        "label": "Eltern-, Schüler- oder Außenkommunikation",
        "terms": [
            "förälder", "foralder", "eltern", "parent", "parents", "schüler",
            "schueler", "elev", "vårdnadshavare", "vardnadshavare", "mail", "e-mail"
        ]
    },
    {
        "key": "BEHOERDE_GERICHT_VERFAHREN",
        "label": "Behörde, Gericht oder Verfahren",
        "terms": [
            "tingsrätt", "tingsratt", "arbetsdomstolen", "domstol", "gericht",
            "förvaltningsrätten", "forvaltningsratten", "skolinspektionen",
            "dnr", "mål nr", "mal nr", "verfahren", "klage", "yttrande", "beslut"
        ]
    },
    {
        "key": "ZEITLICHER_ABLAUF",
        "label": "Zeitlicher Ablauf oder Chronologie",
        "terms": [
            "timeline", "chronologie", "datum", "date", "händelse", "handelse",
            "ereignis", "incident", "vorfall", "protokoll", "logg"
        ]
    },
]

PARTICIPANT_RULES = [
    ("MANDANT_ARBEITNEHMER", ["arbeitnehmer", "arbetstagare", "employee", "lärare", "larare", "lehrer"]),
    ("ARBEITGEBER_KOMMUNE", ["arbeitgeber", "arbetsgivare", "kommun", "skolan", "schule"]),
    ("GERICHT", ["domstol", "tingsrätt", "tingsratt", "arbetsdomstolen", "gericht"]),
    ("BEHOERDE", ["skolinspektionen", "myndighet", "behörde", "behoerde"]),
    ("GEGNERISCHER_ANWALT", ["advokat", "lawyer", "anwalt", "ombud"]),
    ("ELTERN_SCHUELER", ["förälder", "foralder", "eltern", "parent", "elev", "schüler", "schueler"]),
]

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

def tables(con):
    return [x[0] for x in con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()]

def has_columns(con, table, cols):
    have = existing_columns(con, table)
    return all(c.lower() in have for c in cols)

def audit(con, status, agent_job_id, intake_id, details):
    con.execute(
        """
        INSERT INTO agent_fact_context_audit
        (audit_id, audit_time, audit_area, audit_status, agent_job_id, intake_id, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            "agent_sachverhaltsbezug_v1",
            status,
            agent_job_id,
            intake_id,
            details
        ]
    )

def normalize_text(value):
    text = str(value or "")
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def read_text_extract(path):
    try:
        if not path.exists() or not path.is_file():
            return ""

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            return ""

        data = path.read_bytes()[:24000]
        return normalize_text(data.decode("utf-8", errors="ignore"))[:4000]
    except Exception:
        return ""

def read_agent_jobs(con):
    if "agent_work_queue" not in tables(con):
        return []

    needed = [
        "agent_job_id",
        "review_id",
        "intake_id",
        "case_template_key",
        "source_path",
        "original_name",
        "document_language_code",
        "task_key",
        "job_status"
    ]

    if not has_columns(con, "agent_work_queue", needed):
        return []

    rows = con.execute("""
        SELECT agent_job_id, review_id, intake_id, case_template_key, source_path,
               original_name, document_language_code, task_key, job_status
        FROM agent_work_queue
        WHERE task_key = 'SACHVERHALTSBEZUG_VORBEREITEN'
        ORDER BY priority, created_at, original_name
    """).fetchall()

    result = []

    for r in rows:
        result.append({
            "agent_job_id": r[0] or "",
            "review_id": r[1] or "",
            "intake_id": r[2] or "",
            "case_template_key": r[3] or CONFIG_DATA["case_template_key"],
            "source_path": r[4] or "",
            "original_name": r[5] or "",
            "document_language_code": r[6] or "unknown",
            "task_key": r[7] or "",
            "job_status": r[8] or "",
        })

    return result

def read_document_type(con, intake_id):
    if "agent_document_type_suggestion" not in tables(con):
        return ""

    try:
        row = con.execute(
            """
            SELECT suggested_document_type
            FROM agent_document_type_suggestion
            WHERE intake_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [intake_id]
        ).fetchone()

        return row[0] if row and row[0] else ""
    except Exception:
        return ""

def read_language(con, intake_id, fallback):
    if "agent_language_translation_review" in tables(con):
        try:
            row = con.execute(
                """
                SELECT document_language_code, detected_language_code
                FROM agent_language_translation_review
                WHERE intake_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                [intake_id]
            ).fetchone()

            if row:
                return row[0] or row[1] or fallback
        except Exception:
            pass

    return fallback or "unknown"

def find_timeline_date(text):
    patterns = [
        r"\b(20\d{2})[-.](\d{1,2})[-.](\d{1,2})\b",
        r"\b(\d{1,2})[.](\d{1,2})[.](20\d{2})\b",
        r"\b(\d{1,2})[-](\d{1,2})[-](20\d{2})\b"
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if not m:
            continue

        parts = m.groups()

        if len(parts[0]) == 4:
            y = int(parts[0])
            mo = int(parts[1])
            d = int(parts[2])
        else:
            d = int(parts[0])
            mo = int(parts[1])
            y = int(parts[2])

        try:
            return datetime.date(y, mo, d).isoformat()
        except Exception:
            continue

    return ""

def hits_for_terms(text, terms):
    low = text.lower()
    hits = []

    for term in terms:
        if term.lower() in low:
            hits.append(term)

    return hits

def classify_context(filename, text_extract):
    hay = normalize_text((filename or "") + " " + (text_extract or ""))
    best = {
        "key": "SONSTIGES_UNKLAR",
        "label": "Sonstiges oder noch unklarer Sachverhaltsbezug",
        "confidence": "niedrig",
        "reason_terms": []
    }

    for rule in CONTEXT_RULES:
        hits = hits_for_terms(hay, rule["terms"])

        if not hits:
            continue

        confidence = "niedrig"
        if len(hits) >= 4:
            confidence = "hoch"
        elif len(hits) >= 2:
            confidence = "mittel"

        rank = {"niedrig": 1, "mittel": 2, "hoch": 3}

        candidate = {
            "key": rule["key"],
            "label": rule["label"],
            "confidence": confidence,
            "reason_terms": hits
        }

        if rank[candidate["confidence"]] > rank[best["confidence"]] or best["key"] == "SONSTIGES_UNKLAR":
            best = candidate

    return best

def participant_hints(filename, text_extract):
    hay = normalize_text((filename or "") + " " + (text_extract or ""))
    result = []

    for key, terms in PARTICIPANT_RULES:
        hits = hits_for_terms(hay, terms)
        if hits:
            result.append({
                "participant_hint": key,
                "reason_terms": hits
            })

    return result

def fact_context_id(agent_job_id, source_path):
    base = agent_job_id + "|" + source_path + "|fact_context"
    return "FACTCTX_" + hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:20]

def process_job(con, job):
    path = Path(job["source_path"])
    exists = path.exists() and path.is_file()
    filename = job["original_name"] or path.name
    text_extract = read_text_extract(path) if exists else ""

    source_document_type = read_document_type(con, job["intake_id"])
    source_language = read_language(con, job["intake_id"], job["document_language_code"])

    context = classify_context(filename, text_extract)
    participants = participant_hints(filename, text_extract)
    timeline_date = find_timeline_date(filename + " " + text_extract)

    allowed_next = [
        "BEWEIS_ODER_ENTLASTUNG_VORSCHLAG",
        "AUSSAGE_NACHWEIS_KORRESPONDENZ_TRENNEN",
        "ANWALTVORLAGE_FACHLICH_STRUKTURIEREN"
    ]

    status = "SACHVERHALTSBEZUG_VORGESCHLAGEN" if exists else "QUELLDATEI_FEHLT"

    return {
        "fact_context_id": fact_context_id(job["agent_job_id"], job["source_path"]),
        "agent_job_id": job["agent_job_id"],
        "review_id": job["review_id"],
        "intake_id": job["intake_id"],
        "case_template_key": job["case_template_key"],
        "source_path": job["source_path"],
        "original_name": filename,
        "source_document_type": source_document_type,
        "source_document_language_code": source_language,
        "suggested_context_key": context["key"],
        "suggested_context_label": context["label"],
        "confidence": context["confidence"],
        "timeline_hint_date": timeline_date,
        "participant_hints_json": json.dumps(participants, ensure_ascii=False),
        "reason_terms_json": json.dumps(context["reason_terms"], ensure_ascii=False),
        "text_extract": text_extract,
        "allowed_next_agent_tasks_json": json.dumps(allowed_next, ensure_ascii=False),
        "forbidden_conclusions_json": json.dumps(CONFIG_DATA["forbidden_conclusions"], ensure_ascii=False),
        "status": status,
        "notes": CONFIG_DATA["principle"]
    }

def upsert_suggestion(con, s):
    con.execute("DELETE FROM agent_fact_context_suggestion WHERE agent_job_id = ?", [s["agent_job_id"]])

    con.execute(
        """
        INSERT INTO agent_fact_context_suggestion
        (fact_context_id, created_at, updated_at, agent_job_id, review_id, intake_id,
         case_template_key, source_path, original_name, source_document_type,
         source_document_language_code, suggested_context_key, suggested_context_label,
         confidence, timeline_hint_date, participant_hints_json, reason_terms_json,
         text_extract, allowed_next_agent_tasks_json, forbidden_conclusions_json,
         status, notes)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            s["fact_context_id"],
            s["agent_job_id"],
            s["review_id"],
            s["intake_id"],
            s["case_template_key"],
            s["source_path"],
            s["original_name"],
            s["source_document_type"],
            s["source_document_language_code"],
            s["suggested_context_key"],
            s["suggested_context_label"],
            s["confidence"],
            s["timeline_hint_date"],
            s["participant_hints_json"],
            s["reason_terms_json"],
            s["text_extract"],
            s["allowed_next_agent_tasks_json"],
            s["forbidden_conclusions_json"],
            s["status"],
            s["notes"],
        ]
    )

    result_json = json.dumps({
        "suggested_context_key": s["suggested_context_key"],
        "suggested_context_label": s["suggested_context_label"],
        "confidence": s["confidence"],
        "timeline_hint_date": s["timeline_hint_date"],
        "participant_hints": json.loads(s["participant_hints_json"] or "[]"),
        "status": s["status"],
        "note": "Nur vorbereitender Sachverhaltsbezug. Keine Beweiswürdigung."
    }, ensure_ascii=False)

    if "agent_work_queue" in tables(con) and has_columns(con, "agent_work_queue", ["agent_job_id", "job_status", "result_json", "updated_at"]):
        con.execute(
            """
            UPDATE agent_work_queue
            SET job_status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE agent_job_id = ?
            """,
            [
                s["status"],
                result_json,
                s["agent_job_id"]
            ]
        )

def write_reports(suggestions):
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)

    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"AGENT_SACHVERHALTSBEZUG_V1_{ts}.txt"
    csv_file = OUT / f"AGENT_SACHVERHALTSBEZUG_V1_{ts}.csv"
    json_file = OUT / f"AGENT_SACHVERHALTSBEZUG_V1_{ts}.json"

    data = {
        "time": now(),
        "case_template_key": CONFIG_DATA["case_template_key"],
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
        "principle": CONFIG_DATA["principle"],
        "forbidden_conclusions": CONFIG_DATA["forbidden_conclusions"],
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "fact_context_id",
        "agent_job_id",
        "review_id",
        "intake_id",
        "case_template_key",
        "original_name",
        "source_path",
        "source_document_type",
        "source_document_language_code",
        "suggested_context_key",
        "suggested_context_label",
        "confidence",
        "timeline_hint_date",
        "participant_hints_json",
        "reason_terms_json",
        "status",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for s in suggestions:
            writer.writerow({k: s.get(k, "") for k in fields})

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("AGENT SACHVERHALTSBEZUG V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Fallvorlage: " + CONFIG_DATA["case_template_key"] + "\n")
        f.write("Vorschläge: " + str(len(suggestions)) + "\n\n")

        f.write("GRENZE\n")
        f.write("-" * 80 + "\n")
        f.write(CONFIG_DATA["principle"] + "\n\n")
        for item in CONFIG_DATA["forbidden_conclusions"]:
            f.write("- nicht erlaubt: " + item + "\n")

        f.write("\nERGEBNISSE\n")
        f.write("-" * 80 + "\n")

        if not suggestions:
            f.write("Keine offenen Agentenaufgaben SACHVERHALTSBEZUG_VORBEREITEN gefunden.\n")
        else:
            for i, s in enumerate(suggestions, start=1):
                f.write("\n" + str(i) + ". " + s["original_name"] + "\n")
                f.write("Intake-ID: " + s["intake_id"] + "\n")
                f.write("Dokumentart: " + s["source_document_type"] + "\n")
                f.write("Sprache: " + s["source_document_language_code"] + "\n")
                f.write("Sachverhaltsbezug: " + s["suggested_context_label"] + "\n")
                f.write("Schlüssel: " + s["suggested_context_key"] + "\n")
                f.write("Sicherheit: " + s["confidence"] + "\n")
                f.write("Datumshinweis: " + s["timeline_hint_date"] + "\n")
                f.write("Beteiligtenhinweise: " + s["participant_hints_json"] + "\n")
                f.write("Grundbegriffe: " + s["reason_terms_json"] + "\n")
                f.write("Quelle: " + s["source_path"] + "\n")

    return txt, csv_file, json_file

def verify(con):
    count_s = con.execute("SELECT COUNT(*) FROM agent_fact_context_suggestion").fetchone()[0]
    count_a = con.execute("SELECT COUNT(*) FROM agent_fact_context_audit").fetchone()[0]
    return {"suggestion_count": count_s, "audit_count": count_a}

def main():
    con = duckdb.connect(str(DB))
    suggestions = []

    try:
        ensure_schema(con)

        jobs = read_agent_jobs(con)

        for job in jobs:
            try:
                s = process_job(con, job)
                upsert_suggestion(con, s)
                audit(con, "OK", job["agent_job_id"], job["intake_id"], json.dumps({
                    "suggested_context_key": s["suggested_context_key"],
                    "confidence": s["confidence"],
                    "status": s["status"]
                }, ensure_ascii=False))
                suggestions.append(s)
            except Exception as exc:
                audit(con, "FEHLER", job.get("agent_job_id", ""), job.get("intake_id", ""), repr(exc))
                raise

        result = verify(con)
        audit(con, "OK", "", "", json.dumps(result, ensure_ascii=False))

    finally:
        con.close()

    txt, csv_file, json_file = write_reports(suggestions)

    print("")
    print("AGENT_SACHVERHALTSBEZUG_V1 FERTIG")
    print("Vorschläge:", len(suggestions))
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
