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
OUT = LOG / "Agent_Dokumentart"
CONFIG = ROOT / "Config" / "agent_dokumentart_erkennen_v1.json"

OUT.mkdir(parents=True, exist_ok=True)

CONFIG_DATA = {
    "version": "V1",
    "agent": "DOKUMENTART_ERKENNEN",
    "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
    "principle": "Der Agent erkennt nur die formale Dokumentart als Vorschlag. Er bewertet nicht den Beweiswert, die Entlastung oder die rechtliche Relevanz.",
    "allowed_document_type_groups": [
        "Schriftsatz",
        "Korrespondenz",
        "Nachweis",
        "Aussage",
        "Verwaltungsdokument",
        "Protokoll",
        "Bild",
        "Technische Liste",
        "Unklar"
    ],
    "forbidden_conclusions": [
        "Beweiswert",
        "Entlastungswert",
        "rechtliche Relevanz",
        "prozessuale Verwertbarkeit",
        "endgültige Aktenzuordnung",
        "Klageentscheidung"
    ]
}

DDL = [
    """
    CREATE TABLE IF NOT EXISTS agent_document_type_suggestion (
        suggestion_id VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        agent_job_id VARCHAR,
        review_id VARCHAR,
        intake_id VARCHAR,
        case_template_key VARCHAR,
        source_path VARCHAR,
        original_name VARCHAR,
        extension VARCHAR,
        file_exists BOOLEAN,
        size_bytes BIGINT,
        suggested_document_type VARCHAR,
        document_type_group VARCHAR,
        confidence VARCHAR,
        reasons_json VARCHAR,
        extracted_text_hint VARCHAR,
        allowed_next_agent_tasks_json VARCHAR,
        forbidden_conclusions_json VARCHAR,
        status VARCHAR,
        notes VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_document_type_audit (
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
    "agent_document_type_suggestion": [
        ("suggestion_id", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("agent_job_id", "VARCHAR"),
        ("review_id", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("case_template_key", "VARCHAR"),
        ("source_path", "VARCHAR"),
        ("original_name", "VARCHAR"),
        ("extension", "VARCHAR"),
        ("file_exists", "BOOLEAN"),
        ("size_bytes", "BIGINT"),
        ("suggested_document_type", "VARCHAR"),
        ("document_type_group", "VARCHAR"),
        ("confidence", "VARCHAR"),
        ("reasons_json", "VARCHAR"),
        ("extracted_text_hint", "VARCHAR"),
        ("allowed_next_agent_tasks_json", "VARCHAR"),
        ("forbidden_conclusions_json", "VARCHAR"),
        ("status", "VARCHAR"),
        ("notes", "VARCHAR"),
    ],
    "agent_document_type_audit": [
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

def audit(con, status, agent_job_id, intake_id, details):
    con.execute(
        """
        INSERT INTO agent_document_type_audit
        (audit_id, audit_time, audit_area, audit_status, agent_job_id, intake_id, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            "agent_dokumentart_erkennen_v1",
            status,
            agent_job_id,
            intake_id,
            details
        ]
    )

def tables(con):
    return [x[0] for x in con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()]

def read_agent_jobs(con):
    if "agent_work_queue" not in tables(con):
        return []

    rows = con.execute("""
        SELECT agent_job_id, review_id, intake_id, case_template_key, source_path,
               original_name, document_language_code, task_key, job_status
        FROM agent_work_queue
        WHERE task_key = 'DOKUMENTART_ERKENNEN'
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

def normalize_text(value):
    text = str(value or "")
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def read_text_hint(path):
    try:
        if not path.exists() or not path.is_file():
            return ""

        if path.suffix.lower() not in TEXT_EXTENSIONS:
            return ""

        data = path.read_bytes()[:12000]
        return normalize_text(data.decode("utf-8", errors="ignore"))[:2000]
    except Exception:
        return ""

def score_document_type(filename, extension, text_hint):
    hay = (filename + " " + text_hint).lower()
    reasons = []

    def hit(words):
        found = []
        for w in words:
            if w.lower() in hay:
                found.append(w)
        return found

    rules = [
        {
            "type": "Klage oder Schriftsatz",
            "group": "Schriftsatz",
            "words": ["klage", "stämning", "yttrande", "svaromål", "domstol", "tingsrätt", "arbetsdomstolen", "mål nr", "förvaltningsrätten"],
            "base": "mittel"
        },
        {
            "type": "Arbeitsvertrag oder arbeitsrechtliches Personaldokument",
            "group": "Nachweis",
            "words": ["arbetsavtal", "anställning", "employment", "arbeitsvertrag", "anställningsavtal"],
            "base": "mittel"
        },
        {
            "type": "E-Mail oder Korrespondenz",
            "group": "Korrespondenz",
            "words": ["from:", "to:", "subject:", "e-mail", "email", "mail", "brev", "korrespondens"],
            "base": "mittel"
        },
        {
            "type": "Protokoll oder Gesprächsnotiz",
            "group": "Protokoll",
            "words": ["protokoll", "mötesanteckning", "minutes", "meeting", "gespräch", "notiz"],
            "base": "mittel"
        },
        {
            "type": "Meldung oder Anzeige",
            "group": "Verwaltungsdokument",
            "words": ["anmälan", "anmalan", "arbetsmiljö", "arbetsmiljo", "skolinspektionen", "beslut", "dnr"],
            "base": "mittel"
        },
        {
            "type": "Zeitungsartikel oder öffentlicher Bericht",
            "group": "Nachweis",
            "words": ["tidning", "nyheter", "artikel", "granskats", "bericht", "newspaper"],
            "base": "niedrig"
        },
        {
            "type": "Tabelle oder Dateiliste",
            "group": "Technische Liste",
            "words": ["dateiliste", "lista", "förteckning", "excel", "csv", "tabelle"],
            "base": "niedrig"
        },
        {
            "type": "Aussage oder Stellungnahme",
            "group": "Aussage",
            "words": ["uttalande", "statement", "aussage", "förklaring", "erklärung", "witness", "zeuge"],
            "base": "niedrig"
        },
    ]

    best = {
        "suggested_document_type": "Unklare Dokumentart",
        "document_type_group": "Unklar",
        "confidence": "niedrig",
        "reasons": []
    }

    for rule in rules:
        found = hit(rule["words"])
        if found:
            confidence = rule["base"]
            if len(found) >= 3:
                confidence = "hoch"
            elif len(found) == 2 and confidence == "niedrig":
                confidence = "mittel"

            candidate = {
                "suggested_document_type": rule["type"],
                "document_type_group": rule["group"],
                "confidence": confidence,
                "reasons": ["Treffer: " + ", ".join(found)]
            }

            rank = {"niedrig": 1, "mittel": 2, "hoch": 3}
            if rank[candidate["confidence"]] > rank[best["confidence"]] or best["document_type_group"] == "Unklar":
                best = candidate

    if best["document_type_group"] == "Unklar":
        if extension in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
            best = {
                "suggested_document_type": "Bilddatei",
                "document_type_group": "Bild",
                "confidence": "mittel",
                "reasons": ["Dateiendung weist auf Bilddatei hin: " + extension]
            }
        elif extension == ".pdf":
            best = {
                "suggested_document_type": "PDF-Dokument unklarer Art",
                "document_type_group": "Unklar",
                "confidence": "niedrig",
                "reasons": ["PDF erkannt, Inhalt ohne gesonderte Textextraktion nicht sicher bestimmbar."]
            }
        elif extension in {".doc", ".docx", ".odt", ".rtf"}:
            best = {
                "suggested_document_type": "Textdokument unklarer Art",
                "document_type_group": "Unklar",
                "confidence": "niedrig",
                "reasons": ["Textverarbeitungsdatei erkannt, Art noch unklar."]
            }
        elif extension in {".txt", ".md"}:
            best = {
                "suggested_document_type": "Textdatei unklarer Art",
                "document_type_group": "Unklar",
                "confidence": "niedrig",
                "reasons": ["Einfache Textdatei erkannt, Art noch unklar."]
            }
        else:
            best["reasons"] = ["Keine belastbaren Treffer aus Dateiname oder lesbarem Textauszug."]

    return best

def suggestion_id(agent_job_id, source_path):
    base = agent_job_id + "|" + source_path
    return "DOCTYPE_" + hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:20]

def process_job(job):
    path = Path(job["source_path"])
    exists = path.exists() and path.is_file()
    extension = path.suffix.lower() if path.name else ""
    size = path.stat().st_size if exists else 0
    filename = job["original_name"] or path.name
    text_hint = read_text_hint(path) if exists else ""

    guess = score_document_type(filename, extension, text_hint)

    allowed_next = [
        "SPRACHE_UND_UEBERSETZUNG_PRUEFEN",
        "SACHVERHALTSBEZUG_VORBEREITEN",
        "BEWEIS_ODER_ENTLASTUNG_VORSCHLAG",
        "ANWALTVORLAGE_STRUKTURIEREN"
    ]

    return {
        "suggestion_id": suggestion_id(job["agent_job_id"], job["source_path"]),
        "agent_job_id": job["agent_job_id"],
        "review_id": job["review_id"],
        "intake_id": job["intake_id"],
        "case_template_key": job["case_template_key"],
        "source_path": job["source_path"],
        "original_name": filename,
        "extension": extension,
        "file_exists": exists,
        "size_bytes": int(size),
        "suggested_document_type": guess["suggested_document_type"],
        "document_type_group": guess["document_type_group"],
        "confidence": guess["confidence"],
        "reasons_json": json.dumps(guess["reasons"], ensure_ascii=False),
        "extracted_text_hint": text_hint[:2000],
        "allowed_next_agent_tasks_json": json.dumps(allowed_next, ensure_ascii=False),
        "forbidden_conclusions_json": json.dumps(CONFIG_DATA["forbidden_conclusions"], ensure_ascii=False),
        "status": "VORSCHLAG_ERZEUGT" if exists else "QUELLDATEI_FEHLT",
        "notes": CONFIG_DATA["principle"]
    }

def upsert_suggestion(con, s):
    con.execute("DELETE FROM agent_document_type_suggestion WHERE agent_job_id = ?", [s["agent_job_id"]])

    con.execute(
        """
        INSERT INTO agent_document_type_suggestion
        (suggestion_id, created_at, updated_at, agent_job_id, review_id, intake_id,
         case_template_key, source_path, original_name, extension, file_exists, size_bytes,
         suggested_document_type, document_type_group, confidence, reasons_json,
         extracted_text_hint, allowed_next_agent_tasks_json, forbidden_conclusions_json,
         status, notes)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            s["suggestion_id"],
            s["agent_job_id"],
            s["review_id"],
            s["intake_id"],
            s["case_template_key"],
            s["source_path"],
            s["original_name"],
            s["extension"],
            bool(s["file_exists"]),
            int(s["size_bytes"]),
            s["suggested_document_type"],
            s["document_type_group"],
            s["confidence"],
            s["reasons_json"],
            s["extracted_text_hint"],
            s["allowed_next_agent_tasks_json"],
            s["forbidden_conclusions_json"],
            s["status"],
            s["notes"],
        ]
    )

    result_json = json.dumps({
        "suggested_document_type": s["suggested_document_type"],
        "document_type_group": s["document_type_group"],
        "confidence": s["confidence"],
        "status": s["status"],
        "forbidden_conclusions": CONFIG_DATA["forbidden_conclusions"],
        "note": "Formaler Vorschlag. Keine abschließende Bewertung."
    }, ensure_ascii=False)

    if "agent_work_queue" in tables(con):
        con.execute(
            """
            UPDATE agent_work_queue
            SET job_status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE agent_job_id = ?
            """,
            [
                "VORSCHLAG_ERZEUGT" if s["file_exists"] else "QUELLDATEI_FEHLT",
                result_json,
                s["agent_job_id"]
            ]
        )

def write_reports(suggestions):
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)

    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"AGENT_DOKUMENTART_ERKENNEN_V1_{ts}.txt"
    csv_file = OUT / f"AGENT_DOKUMENTART_ERKENNEN_V1_{ts}.csv"
    json_file = OUT / f"AGENT_DOKUMENTART_ERKENNEN_V1_{ts}.json"

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
        "suggestion_id",
        "agent_job_id",
        "review_id",
        "intake_id",
        "case_template_key",
        "original_name",
        "source_path",
        "extension",
        "file_exists",
        "size_bytes",
        "suggested_document_type",
        "document_type_group",
        "confidence",
        "status",
        "reasons_json",
        "notes",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for s in suggestions:
            writer.writerow({k: s.get(k, "") for k in fields})

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("AGENT DOKUMENTART ERKENNEN V1\n")
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
            f.write("Keine offenen Agentenaufgaben DOKUMENTART_ERKENNEN gefunden.\n")
        else:
            for i, s in enumerate(suggestions, start=1):
                f.write("\n" + str(i) + ". " + s["original_name"] + "\n")
                f.write("Intake-ID: " + s["intake_id"] + "\n")
                f.write("Vorschlag: " + s["suggested_document_type"] + "\n")
                f.write("Gruppe: " + s["document_type_group"] + "\n")
                f.write("Sicherheit: " + s["confidence"] + "\n")
                f.write("Status: " + s["status"] + "\n")
                f.write("Quelle: " + s["source_path"] + "\n")
                f.write("Gründe: " + s["reasons_json"] + "\n")

    return txt, csv_file, json_file

def verify(con):
    suggestion_count = con.execute("SELECT COUNT(*) FROM agent_document_type_suggestion").fetchone()[0]
    audit_count = con.execute("SELECT COUNT(*) FROM agent_document_type_audit").fetchone()[0]

    return {
        "suggestion_count": suggestion_count,
        "audit_count": audit_count
    }

def main():
    con = duckdb.connect(str(DB))
    suggestions = []

    try:
        ensure_schema(con)

        jobs = read_agent_jobs(con)

        for job in jobs:
            try:
                s = process_job(job)
                upsert_suggestion(con, s)
                audit(con, "OK", job["agent_job_id"], job["intake_id"], json.dumps({
                    "suggested_document_type": s["suggested_document_type"],
                    "confidence": s["confidence"],
                    "status": s["status"]
                }, ensure_ascii=False))
                suggestions.append(s)
            except Exception as exc:
                audit(con, "FEHLER", job.get("agent_job_id", ""), job.get("intake_id", ""), repr(exc))
                raise

        result = verify(con)
        audit(con, "OK", "", "", json.dumps(result, ensure_ascii=False))

    except Exception:
        raise
    finally:
        con.close()

    txt, csv_file, json_file = write_reports(suggestions)

    print("")
    print("AGENT_DOKUMENTART_ERKENNEN_V1 FERTIG")
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
