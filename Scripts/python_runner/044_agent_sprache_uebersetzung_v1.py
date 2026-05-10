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
OUT = LOG / "Agent_Sprache_Uebersetzung"
TRANSLATION_DIR = ROOT / "Posteingang" / "96_Uebersetzung_DE"
CONFIG = ROOT / "Config" / "agent_sprache_uebersetzung_v1.json"

OUT.mkdir(parents=True, exist_ok=True)
TRANSLATION_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_DATA = {
    "version": "V1",
    "agent": "SPRACHE_UND_UEBERSETZUNG_PRUEFEN",
    "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
    "target_language_code": "de",
    "case_context": {
        "official_language_code": "sv",
        "procedural_language_code": "sv",
        "internal_work_language_code": "de"
    },
    "principle": "Der Agent prüft Sprache und bereitet eine grobe deutsche Arbeitsübersetzung vor. Er erstellt keine beglaubigte Übersetzung und keine rechtliche Bewertung.",
    "forbidden_conclusions": [
        "beglaubigte Übersetzung",
        "Beweiswert",
        "Entlastungswert",
        "rechtliche Relevanz",
        "prozessuale Verwertbarkeit",
        "endgültige Aktenzuordnung"
    ]
}

DDL = [
    """
    CREATE TABLE IF NOT EXISTS agent_language_translation_review (
        translation_review_id VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        agent_job_id VARCHAR,
        review_id VARCHAR,
        intake_id VARCHAR,
        case_template_key VARCHAR,
        source_path VARCHAR,
        original_name VARCHAR,
        document_language_code VARCHAR,
        detected_language_code VARCHAR,
        additional_languages_json VARCHAR,
        is_multilingual BOOLEAN,
        target_language_code VARCHAR,
        rough_translation_required BOOLEAN,
        rough_translation_possible BOOLEAN,
        rough_translation_status VARCHAR,
        rough_translation_path VARCHAR,
        source_text_extract VARCHAR,
        translation_note VARCHAR,
        confidence VARCHAR,
        forbidden_conclusions_json VARCHAR,
        status VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_language_translation_audit (
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
    "agent_language_translation_review": [
        ("translation_review_id", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("agent_job_id", "VARCHAR"),
        ("review_id", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("case_template_key", "VARCHAR"),
        ("source_path", "VARCHAR"),
        ("original_name", "VARCHAR"),
        ("document_language_code", "VARCHAR"),
        ("detected_language_code", "VARCHAR"),
        ("additional_languages_json", "VARCHAR"),
        ("is_multilingual", "BOOLEAN"),
        ("target_language_code", "VARCHAR"),
        ("rough_translation_required", "BOOLEAN"),
        ("rough_translation_possible", "BOOLEAN"),
        ("rough_translation_status", "VARCHAR"),
        ("rough_translation_path", "VARCHAR"),
        ("source_text_extract", "VARCHAR"),
        ("translation_note", "VARCHAR"),
        ("confidence", "VARCHAR"),
        ("forbidden_conclusions_json", "VARCHAR"),
        ("status", "VARCHAR"),
    ],
    "agent_language_translation_audit": [
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

SV_MARKERS = [
    "och", "detta", "är", "för", "att", "domstol", "tingsrätt", "arbetsgivare",
    "arbetstagare", "arbetsrätt", "anställning", "skola", "kommun", "mål nr",
    "yttrande", "beslut", "anmälan"
]

DE_MARKERS = [
    "und", "dies", "ist", "gericht", "arbeitnehmer", "arbeitgeber", "arbeitsrecht",
    "schrift", "schriftsatz", "nachweis", "anlage", "kündigung", "entscheidung"
]

EN_MARKERS = [
    "and", "this", "court", "employee", "employer", "employment", "statement",
    "evidence", "document", "case", "lawyer", "school"
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

def audit(con, status, agent_job_id, intake_id, details):
    con.execute(
        """
        INSERT INTO agent_language_translation_audit
        (audit_id, audit_time, audit_area, audit_status, agent_job_id, intake_id, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            "agent_sprache_uebersetzung_v1",
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

def score_lang(text, markers):
    low = " " + text.lower() + " "
    score = 0
    for m in markers:
        token = m.lower()
        if " " + token + " " in low or token in low:
            score += 1
    return score

def detect_languages(text, filename):
    hay = normalize_text((filename or "") + " " + (text or ""))

    scores = {
        "sv": score_lang(hay, SV_MARKERS),
        "de": score_lang(hay, DE_MARKERS),
        "en": score_lang(hay, EN_MARKERS),
    }

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    primary = "unknown"
    confidence = "niedrig"

    if ranked and ranked[0][1] > 0:
        primary = ranked[0][0]
        if ranked[0][1] >= 5:
            confidence = "hoch"
        elif ranked[0][1] >= 2:
            confidence = "mittel"

    additional = []
    for code, score in ranked[1:]:
        if score >= 2:
            additional.append(code)

    is_multilingual = len(additional) > 0

    return primary, additional, is_multilingual, confidence, scores

def read_document_profile(con, intake_id, source_path):
    names = tables(con)

    if "posteingang_document_language_profile" not in names:
        return {}

    try:
        rows = con.execute(
            """
            SELECT detected_primary_language_code,
                   detected_additional_languages_json,
                   is_multilingual,
                   rough_translation_required,
                   rough_translation_target_language_code,
                   confidence
            FROM posteingang_document_language_profile
            WHERE intake_id = ?
               OR source_path = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [intake_id, source_path]
        ).fetchall()

        if not rows:
            return {}

        r = rows[0]
        return {
            "detected_primary_language_code": r[0] or "",
            "detected_additional_languages_json": r[1] or "[]",
            "is_multilingual": bool(r[2]),
            "rough_translation_required": bool(r[3]),
            "rough_translation_target_language_code": r[4] or "de",
            "confidence": r[5] or "niedrig"
        }
    except Exception:
        return {}

def read_agent_jobs(con):
    if "agent_work_queue" not in tables(con):
        return []

    rows = con.execute("""
        SELECT agent_job_id, review_id, intake_id, case_template_key, source_path,
               original_name, document_language_code, rough_translation_target_language_code,
               task_key, job_status
        FROM agent_work_queue
        WHERE task_key = 'SPRACHE_UND_UEBERSETZUNG_PRUEFEN'
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
            "rough_translation_target_language_code": r[7] or "de",
            "task_key": r[8] or "",
            "job_status": r[9] or "",
        })

    return result

def review_id(agent_job_id, source_path):
    base = agent_job_id + "|" + source_path + "|language_translation"
    return "LANGTRANS_" + hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:20]

def make_translation_note(source_lang, target_lang, text_extract, path_exists, extension):
    if not path_exists:
        return "Quelldatei fehlt. Arbeitsübersetzung kann erst nach Wiederherstellung der Datei erstellt werden.", False, "QUELLDATEI_FEHLT"

    if source_lang == "de":
        return "Dokument ist bereits deutsch oder überwiegend deutsch. Grobe Arbeitsübersetzung nach Deutsch ist nicht erforderlich.", True, "NICHT_ERFORDERLICH"

    if not text_extract:
        return "Direkter Textauszug ist in V1 nicht verfügbar. Für PDF, DOCX, Bild oder Scan ist OCR, Parser oder externe KI-Übersetzung nachzulagern.", True, "TECHNISCH_VORBEREITET"

    return "Grobe deutsche Arbeitsübersetzung ist technisch möglich. V1 speichert den Ausgangstext und markiert die maschinelle Übersetzung nach Deutsch als nächsten Verarbeitungsschritt.", True, "MASCHINELLE_UEBERSETZUNG_VORBEREITET"

def write_translation_file(s):
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", s["intake_id"] or s["translation_review_id"])
    path = TRANSLATION_DIR / (safe + "_arbeitsuebersetzung_de.txt")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("GROBE ARBEITSUEBERSETZUNG NACH DEUTSCH\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Intake-ID: " + s["intake_id"] + "\n")
        f.write("Originalname: " + s["original_name"] + "\n")
        f.write("Quelle: " + s["source_path"] + "\n")
        f.write("Erkannte Sprache: " + s["detected_language_code"] + "\n")
        f.write("Zielsprache: de\n")
        f.write("Status: " + s["rough_translation_status"] + "\n\n")

        f.write("HINWEIS\n")
        f.write("-" * 80 + "\n")
        f.write(s["translation_note"] + "\n\n")

        f.write("AUSGANGSTEXTAUSZUG\n")
        f.write("-" * 80 + "\n")
        if s["source_text_extract"]:
            f.write(s["source_text_extract"] + "\n")
        else:
            f.write("Kein direkt lesbarer Textauszug vorhanden.\n")

        f.write("\nGRENZE\n")
        f.write("-" * 80 + "\n")
        f.write("Dies ist keine beglaubigte Übersetzung und keine rechtliche Bewertung.\n")

    return str(path)

def process_job(con, job):
    path = Path(job["source_path"])
    exists = path.exists() and path.is_file()
    extension = path.suffix.lower() if path.name else ""
    text_extract = read_text_extract(path) if exists else ""

    profile = read_document_profile(con, job["intake_id"], job["source_path"])

    detected, additional, multilingual, confidence, scores = detect_languages(text_extract, job["original_name"] or path.name)

    if profile.get("detected_primary_language_code"):
        detected = profile.get("detected_primary_language_code") or detected
        try:
            additional = json.loads(profile.get("detected_additional_languages_json") or "[]")
        except Exception:
            additional = []
        multilingual = bool(profile.get("is_multilingual"))
        confidence = profile.get("confidence") or confidence

    document_language = job["document_language_code"]
    if not document_language or document_language == "unknown":
        document_language = detected

    target = job["rough_translation_target_language_code"] or "de"
    if target != "de":
        target = "de"

    rough_required = document_language != "de"
    if profile:
        rough_required = bool(profile.get("rough_translation_required")) or document_language != "de"

    note, possible, translation_status = make_translation_note(document_language, target, text_extract, exists, extension)

    s = {
        "translation_review_id": review_id(job["agent_job_id"], job["source_path"]),
        "agent_job_id": job["agent_job_id"],
        "review_id": job["review_id"],
        "intake_id": job["intake_id"],
        "case_template_key": job["case_template_key"],
        "source_path": job["source_path"],
        "original_name": job["original_name"] or path.name,
        "document_language_code": document_language or "unknown",
        "detected_language_code": detected or "unknown",
        "additional_languages_json": json.dumps(additional, ensure_ascii=False),
        "is_multilingual": bool(multilingual),
        "target_language_code": "de",
        "rough_translation_required": bool(rough_required),
        "rough_translation_possible": bool(possible),
        "rough_translation_status": translation_status,
        "rough_translation_path": "",
        "source_text_extract": text_extract,
        "translation_note": note,
        "confidence": confidence,
        "forbidden_conclusions_json": json.dumps(CONFIG_DATA["forbidden_conclusions"], ensure_ascii=False),
        "status": "SPRACHPRUEFUNG_ERLEDIGT" if possible else "SPRACHPRUEFUNG_OFFEN"
    }

    s["rough_translation_path"] = write_translation_file(s)

    return s

def upsert_review(con, s):
    con.execute("DELETE FROM agent_language_translation_review WHERE agent_job_id = ?", [s["agent_job_id"]])

    con.execute(
        """
        INSERT INTO agent_language_translation_review
        (translation_review_id, created_at, updated_at, agent_job_id, review_id, intake_id,
         case_template_key, source_path, original_name, document_language_code,
         detected_language_code, additional_languages_json, is_multilingual,
         target_language_code, rough_translation_required, rough_translation_possible,
         rough_translation_status, rough_translation_path, source_text_extract,
         translation_note, confidence, forbidden_conclusions_json, status)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            s["translation_review_id"],
            s["agent_job_id"],
            s["review_id"],
            s["intake_id"],
            s["case_template_key"],
            s["source_path"],
            s["original_name"],
            s["document_language_code"],
            s["detected_language_code"],
            s["additional_languages_json"],
            bool(s["is_multilingual"]),
            s["target_language_code"],
            bool(s["rough_translation_required"]),
            bool(s["rough_translation_possible"]),
            s["rough_translation_status"],
            s["rough_translation_path"],
            s["source_text_extract"],
            s["translation_note"],
            s["confidence"],
            s["forbidden_conclusions_json"],
            s["status"],
        ]
    )

    result_json = json.dumps({
        "document_language_code": s["document_language_code"],
        "detected_language_code": s["detected_language_code"],
        "is_multilingual": s["is_multilingual"],
        "target_language_code": s["target_language_code"],
        "rough_translation_required": s["rough_translation_required"],
        "rough_translation_possible": s["rough_translation_possible"],
        "rough_translation_status": s["rough_translation_status"],
        "rough_translation_path": s["rough_translation_path"],
        "status": s["status"],
        "note": "Sprach- und Übersetzungsvorschlag. Keine beglaubigte Übersetzung."
    }, ensure_ascii=False)

    if "agent_work_queue" in tables(con):
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

def write_reports(reviews):
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)

    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"AGENT_SPRACHE_UEBERSETZUNG_V1_{ts}.txt"
    csv_file = OUT / f"AGENT_SPRACHE_UEBERSETZUNG_V1_{ts}.csv"
    json_file = OUT / f"AGENT_SPRACHE_UEBERSETZUNG_V1_{ts}.json"

    data = {
        "time": now(),
        "case_template_key": CONFIG_DATA["case_template_key"],
        "reviews_count": len(reviews),
        "reviews": reviews,
        "principle": CONFIG_DATA["principle"],
        "forbidden_conclusions": CONFIG_DATA["forbidden_conclusions"],
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "translation_review_id",
        "agent_job_id",
        "review_id",
        "intake_id",
        "case_template_key",
        "original_name",
        "source_path",
        "document_language_code",
        "detected_language_code",
        "additional_languages_json",
        "is_multilingual",
        "target_language_code",
        "rough_translation_required",
        "rough_translation_possible",
        "rough_translation_status",
        "rough_translation_path",
        "confidence",
        "status",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for r in reviews:
            writer.writerow({k: r.get(k, "") for k in fields})

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("AGENT SPRACHE UND UEBERSETZUNG V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Fallvorlage: " + CONFIG_DATA["case_template_key"] + "\n")
        f.write("Prüfungen: " + str(len(reviews)) + "\n\n")

        f.write("GRENZE\n")
        f.write("-" * 80 + "\n")
        f.write(CONFIG_DATA["principle"] + "\n\n")
        for item in CONFIG_DATA["forbidden_conclusions"]:
            f.write("- nicht erlaubt: " + item + "\n")

        f.write("\nERGEBNISSE\n")
        f.write("-" * 80 + "\n")

        if not reviews:
            f.write("Keine offenen Agentenaufgaben SPRACHE_UND_UEBERSETZUNG_PRUEFEN gefunden.\n")
        else:
            for i, r in enumerate(reviews, start=1):
                f.write("\n" + str(i) + ". " + r["original_name"] + "\n")
                f.write("Intake-ID: " + r["intake_id"] + "\n")
                f.write("Dokumentsprache: " + r["document_language_code"] + "\n")
                f.write("Erkannte Sprache: " + r["detected_language_code"] + "\n")
                f.write("Mehrsprachig: " + str(r["is_multilingual"]) + "\n")
                f.write("Zielsprache: " + r["target_language_code"] + "\n")
                f.write("Arbeitsübersetzung erforderlich: " + str(r["rough_translation_required"]) + "\n")
                f.write("Arbeitsübersetzung möglich: " + str(r["rough_translation_possible"]) + "\n")
                f.write("Status: " + r["rough_translation_status"] + "\n")
                f.write("Übersetzungsdatei: " + r["rough_translation_path"] + "\n")
                f.write("Hinweis: " + r["translation_note"] + "\n")

    return txt, csv_file, json_file

def verify(con):
    review_count = con.execute("SELECT COUNT(*) FROM agent_language_translation_review").fetchone()[0]
    audit_count = con.execute("SELECT COUNT(*) FROM agent_language_translation_audit").fetchone()[0]

    return {
        "review_count": review_count,
        "audit_count": audit_count
    }

def main():
    con = duckdb.connect(str(DB))
    reviews = []

    try:
        ensure_schema(con)

        jobs = read_agent_jobs(con)

        for job in jobs:
            try:
                r = process_job(con, job)
                upsert_review(con, r)
                audit(con, "OK", job["agent_job_id"], job["intake_id"], json.dumps({
                    "document_language_code": r["document_language_code"],
                    "detected_language_code": r["detected_language_code"],
                    "rough_translation_status": r["rough_translation_status"],
                    "status": r["status"]
                }, ensure_ascii=False))
                reviews.append(r)
            except Exception as exc:
                audit(con, "FEHLER", job.get("agent_job_id", ""), job.get("intake_id", ""), repr(exc))
                raise

        result = verify(con)
        audit(con, "OK", "", "", json.dumps(result, ensure_ascii=False))

    finally:
        con.close()

    txt, csv_file, json_file = write_reports(reviews)

    print("")
    print("AGENT_SPRACHE_UEBERSETZUNG_V1 FERTIG")
    print("Prüfungen:", len(reviews))
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("Übersetzungsordner:", TRANSLATION_DIR)
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
