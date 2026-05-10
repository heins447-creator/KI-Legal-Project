# -*- coding: utf-8 -*-
import sys
import json
import csv
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
POST = ROOT / "Posteingang"
LOG = ROOT / "Windows_App" / "Logs"
OUT = LOG / "Anwaltvorlagen"
CONFIG = ROOT / "Config" / "anwaltvorlage_grundmodul_v1.json"

DIRS = {
    "anwalt": POST / "04_Anwaltvorlage",
    "sicherheit": POST / "92_Sicherheitsberichte",
    "sprachen": POST / "93_Sprachberichte",
    "dokumentsprache": POST / "95_Dokumentsprachprofile",
    "uebersetzung": POST / "96_Uebersetzung_DE",
    "schlusskontrolle": POST / "97_Schlusskontrolle",
}

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

CONFIG_DATA = {
    "version": "V1",
    "module": "Anwaltvorlage Grundmodul",
    "case_template_key": "TEMPLATE_SE_ARBEITSRECHT",
    "case_context": {
        "matter_type": "Schwedischer Arbeitsrechtsstreit",
        "parties_context": "Arbeitnehmer gegen kommunalen Arbeitgeber",
        "jurisdiction_country_code": "SE",
        "official_language_code": "sv",
        "procedural_language_code": "sv",
        "internal_work_language_code": "de",
        "rough_translation_target_language_code": "de"
    },
    "minimum_for_lawyer_review": [
        "technisch sicher oder durch Vorzimmer freigegeben",
        "Posteingang bearbeitet",
        "Sprache erkannt oder als unklar markiert",
        "grobe Arbeitsübersetzung nach Deutsch möglich oder als erforderlich markiert",
        "Anwaltvorlage organisatorisch erzeugt"
    ],
    "not_decided_here": [
        "Beweiswert",
        "Entlastungswert",
        "rechtliche Relevanz",
        "Aussagequalität",
        "endgültige Aktenzuordnung",
        "Klageentscheidung"
    ]
}

DDL = [
    """
    CREATE TABLE IF NOT EXISTS anwalt_review_queue (
        review_id VARCHAR,
        intake_id VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        case_template_key VARCHAR,
        source_path VARCHAR,
        original_name VARCHAR,
        document_language_code VARCHAR,
        detected_languages_json VARCHAR,
        rough_translation_target_language_code VARCHAR,
        rough_translation_available BOOLEAN,
        rough_translation_path VARCHAR,
        safety_status VARCHAR,
        post_intake_status VARCHAR,
        lawyer_review_status VARCHAR,
        minimum_check_json VARCHAR,
        next_required_action VARCHAR,
        notes VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS anwalt_review_audit (
        audit_id VARCHAR,
        audit_time TIMESTAMP,
        audit_area VARCHAR,
        audit_status VARCHAR,
        intake_id VARCHAR,
        details VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS anwalt_case_context_template (
        template_key VARCHAR,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        jurisdiction_country_code VARCHAR,
        official_language_code VARCHAR,
        procedural_language_code VARCHAR,
        internal_work_language_code VARCHAR,
        rough_translation_target_language_code VARCHAR,
        matter_type VARCHAR,
        parties_context VARCHAR,
        notes VARCHAR
    )
    """
]

REQUIRED_COLUMNS = {
    "anwalt_review_queue": [
        ("review_id", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("case_template_key", "VARCHAR"),
        ("source_path", "VARCHAR"),
        ("original_name", "VARCHAR"),
        ("document_language_code", "VARCHAR"),
        ("detected_languages_json", "VARCHAR"),
        ("rough_translation_target_language_code", "VARCHAR"),
        ("rough_translation_available", "BOOLEAN"),
        ("rough_translation_path", "VARCHAR"),
        ("safety_status", "VARCHAR"),
        ("post_intake_status", "VARCHAR"),
        ("lawyer_review_status", "VARCHAR"),
        ("minimum_check_json", "VARCHAR"),
        ("next_required_action", "VARCHAR"),
        ("notes", "VARCHAR"),
    ],
    "anwalt_review_audit": [
        ("audit_id", "VARCHAR"),
        ("audit_time", "TIMESTAMP"),
        ("audit_area", "VARCHAR"),
        ("audit_status", "VARCHAR"),
        ("intake_id", "VARCHAR"),
        ("details", "VARCHAR"),
    ],
    "anwalt_case_context_template": [
        ("template_key", "VARCHAR"),
        ("created_at", "TIMESTAMP"),
        ("updated_at", "TIMESTAMP"),
        ("jurisdiction_country_code", "VARCHAR"),
        ("official_language_code", "VARCHAR"),
        ("procedural_language_code", "VARCHAR"),
        ("internal_work_language_code", "VARCHAR"),
        ("rough_translation_target_language_code", "VARCHAR"),
        ("matter_type", "VARCHAR"),
        ("parties_context", "VARCHAR"),
        ("notes", "VARCHAR"),
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

def audit(con, status, intake_id, details):
    con.execute(
        """
        INSERT INTO anwalt_review_audit
        (audit_id, audit_time, audit_area, audit_status, intake_id, details)
        VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            "anwaltvorlage_grundmodul_v1",
            status,
            intake_id,
            details
        ]
    )

def active_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def extract_intake_id(path):
    stem = path.stem

    for suffix in [
        "_entscheidungskarte",
        "_sicherheitskarte",
        "_sprachkarte",
        "_sicherheitsbericht",
        "_sprachbericht",
        "_dokumentsprachprofil",
        "_schlusskontrolle",
    ]:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]

    if "__" in stem:
        return stem.split("__", 1)[0]

    parts = stem.split("_")
    if len(parts) >= 2 and parts[0].isdigit():
        return parts[0] + "_" + parts[1]

    return stem

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def first_existing(files):
    return str(files[0]) if files else ""

def index_by_intake(path):
    index = {}
    for file in active_files(path):
        intake = extract_intake_id(file)
        index.setdefault(intake, []).append(file)
    return index

def find_language_profile(intake, doc_index, sprach_index):
    candidates = doc_index.get(intake, []) + sprach_index.get(intake, [])

    for c in candidates:
        if c.suffix.lower() == ".json":
            data = read_json(c)
            if data:
                return c, data

    return None, {}

def find_translation(intake, trans_index):
    candidates = trans_index.get(intake, [])
    return first_existing(candidates)

def build_review_rows():
    doc_index = index_by_intake(DIRS["dokumentsprache"])
    sprach_index = index_by_intake(DIRS["sprachen"])
    sicher_index = index_by_intake(DIRS["sicherheit"])
    trans_index = index_by_intake(DIRS["uebersetzung"])
    schluss_index = index_by_intake(DIRS["schlusskontrolle"])

    rows = []

    for file in active_files(DIRS["anwalt"]):
        intake = extract_intake_id(file)

        language_profile_path, language_data = find_language_profile(intake, doc_index, sprach_index)
        translation_path = find_translation(intake, trans_index)

        security_files = sicher_index.get(intake, [])
        schluss_files = schluss_index.get(intake, [])

        document_language = (
            language_data.get("primary_language_code")
            or language_data.get("detected_actual_language_code")
            or language_data.get("document_language_code")
            or "unknown"
        )

        detected_languages = (
            language_data.get("detected_languages")
            or language_data.get("detected_languages_json")
            or [document_language]
        )

        if isinstance(detected_languages, str):
            try:
                detected_languages_json = json.dumps(json.loads(detected_languages), ensure_ascii=False)
            except Exception:
                detected_languages_json = json.dumps([detected_languages], ensure_ascii=False)
        else:
            detected_languages_json = json.dumps(detected_languages, ensure_ascii=False)

        rough_target = (
            language_data.get("rough_translation_target_language_code")
            or language_data.get("target_work_language_code")
            or "de"
        )

        rough_available = bool(translation_path) or document_language == "de"

        minimum_check = {
            "sicher": bool(security_files) or True,
            "bearbeitet": True,
            "sprache_erkannt": document_language != "unknown",
            "grobe_uebersetzung_deutsch_moeglich": rough_available or rough_target == "de",
            "anwaltvorlage_bereit": True,
            "hinweis": "Diese Prüfung ist formell. Inhaltliche Bewertung bleibt nachgelagert."
        }

        if minimum_check["sprache_erkannt"] and minimum_check["grobe_uebersetzung_deutsch_moeglich"]:
            next_action = "ANWALT_SICHTUNG"
            review_status = "VORLAGE_BEREIT"
        elif not minimum_check["sprache_erkannt"]:
            next_action = "SPRACHE_MANUELL_PRUEFEN"
            review_status = "VORLAGE_MIT_HINWEIS"
        else:
            next_action = "GROBE_UEBERSETZUNG_DE_ERZEUGEN_ODER_MARKIEREN"
            review_status = "VORLAGE_MIT_HINWEIS"

        rows.append({
            "review_id": "REV_" + hashlib.sha256((intake + "|" + str(file)).encode("utf-8", errors="ignore")).hexdigest()[:16],
            "intake_id": intake,
            "case_template_key": CONFIG_DATA["case_template_key"],
            "source_path": str(file),
            "original_name": file.name,
            "document_language_code": document_language,
            "detected_languages_json": detected_languages_json,
            "rough_translation_target_language_code": rough_target,
            "rough_translation_available": rough_available,
            "rough_translation_path": translation_path,
            "safety_status": "FORMELL_POSTEINGANG_FREIGEGEBEN" if security_files else "SICHERHEITSNACHWEIS_NICHT_ZUGEORDNET",
            "post_intake_status": "ANWALTVORLAGE",
            "lawyer_review_status": review_status,
            "minimum_check_json": json.dumps(minimum_check, ensure_ascii=False),
            "next_required_action": next_action,
            "notes": "Keine Beweiswürdigung. Keine Entlastungsbewertung. Keine endgültige Aktenzuordnung.",
            "language_profile_path": str(language_profile_path) if language_profile_path else "",
            "security_reports": [str(x) for x in security_files],
            "schlusskontrolle": [str(x) for x in schluss_files],
        })

    return rows

def upsert_case_context(con):
    c = CONFIG_DATA["case_context"]

    con.execute(
        "DELETE FROM anwalt_case_context_template WHERE template_key = ?",
        [CONFIG_DATA["case_template_key"]]
    )

    con.execute(
        """
        INSERT INTO anwalt_case_context_template
        (template_key, created_at, updated_at, jurisdiction_country_code,
         official_language_code, procedural_language_code, internal_work_language_code,
         rough_translation_target_language_code, matter_type, parties_context, notes)
        VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            CONFIG_DATA["case_template_key"],
            c["jurisdiction_country_code"],
            c["official_language_code"],
            c["procedural_language_code"],
            c["internal_work_language_code"],
            c["rough_translation_target_language_code"],
            c["matter_type"],
            c["parties_context"],
            "Schweden-Arbeitsrecht: Verfahrenssprache Schwedisch, interne Arbeitssprache Deutsch."
        ]
    )

def upsert_review_queue(con, rows):
    for r in rows:
        con.execute("DELETE FROM anwalt_review_queue WHERE source_path = ?", [r["source_path"]])

        con.execute(
            """
            INSERT INTO anwalt_review_queue
            (review_id, intake_id, created_at, updated_at, case_template_key,
             source_path, original_name, document_language_code, detected_languages_json,
             rough_translation_target_language_code, rough_translation_available,
             rough_translation_path, safety_status, post_intake_status, lawyer_review_status,
             minimum_check_json, next_required_action, notes)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                r["review_id"],
                r["intake_id"],
                r["case_template_key"],
                r["source_path"],
                r["original_name"],
                r["document_language_code"],
                r["detected_languages_json"],
                r["rough_translation_target_language_code"],
                bool(r["rough_translation_available"]),
                r["rough_translation_path"],
                r["safety_status"],
                r["post_intake_status"],
                r["lawyer_review_status"],
                r["minimum_check_json"],
                r["next_required_action"],
                r["notes"]
            ]
        )

def write_reports(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)

    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"ANWALTVORLAGE_GRUNDMODUL_V1_{ts}.txt"
    csv_file = OUT / f"ANWALTVORLAGE_GRUNDMODUL_V1_{ts}.csv"
    json_file = OUT / f"ANWALTVORLAGE_GRUNDMODUL_V1_{ts}.json"

    data = {
        "time": now(),
        "case_template_key": CONFIG_DATA["case_template_key"],
        "rows_count": len(rows),
        "rows": rows,
        "boundary": CONFIG_DATA["not_decided_here"],
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "review_id",
        "intake_id",
        "case_template_key",
        "original_name",
        "source_path",
        "document_language_code",
        "detected_languages_json",
        "rough_translation_target_language_code",
        "rough_translation_available",
        "rough_translation_path",
        "safety_status",
        "post_intake_status",
        "lawyer_review_status",
        "next_required_action",
        "language_profile_path",
        "notes",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("ANWALTVORLAGE GRUNDMODUL V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Fallvorlage: " + CONFIG_DATA["case_template_key"] + "\n")
        f.write("Vorlagen: " + str(len(rows)) + "\n\n")

        f.write("KONTEXT\n")
        f.write("-" * 80 + "\n")
        for k, v in CONFIG_DATA["case_context"].items():
            f.write(k + ": " + str(v) + "\n")

        f.write("\nGRENZE\n")
        f.write("-" * 80 + "\n")
        for item in CONFIG_DATA["not_decided_here"]:
            f.write("- " + item + "\n")

        f.write("\nANWALTVORLAGEN\n")
        f.write("-" * 80 + "\n")

        if not rows:
            f.write("Keine Dateien in Posteingang/04_Anwaltvorlage gefunden.\n")
        else:
            for i, row in enumerate(rows, start=1):
                f.write("\n" + str(i) + ". " + row["original_name"] + "\n")
                f.write("Intake-ID: " + row["intake_id"] + "\n")
                f.write("Sprache: " + row["document_language_code"] + "\n")
                f.write("Übersetzung Deutsch möglich: " + str(row["rough_translation_available"]) + "\n")
                f.write("Status: " + row["lawyer_review_status"] + "\n")
                f.write("Nächster Schritt: " + row["next_required_action"] + "\n")
                f.write("Quelle: " + row["source_path"] + "\n")

    return txt, csv_file, json_file

def verify(con):
    queue_count = con.execute("SELECT COUNT(*) FROM anwalt_review_queue").fetchone()[0]
    template = con.execute("""
        SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
               internal_work_language_code, rough_translation_target_language_code
        FROM anwalt_case_context_template
        WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
    """).fetchone()

    if tuple(template or ()) != ("SE", "sv", "sv", "de", "de"):
        raise RuntimeError("Anwalt-Fallkontext Schweden Arbeitsrecht ist fehlerhaft: " + repr(template))

    return {
        "queue_count": queue_count,
        "template": tuple(template)
    }

def main():
    con = duckdb.connect(str(DB))
    try:
        ensure_schema(con)
        upsert_case_context(con)
        rows = build_review_rows()
        upsert_review_queue(con, rows)
        result = verify(con)
        audit(con, "OK", "", json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        try:
            audit(con, "FEHLER", "", repr(exc))
        except Exception:
            pass
        raise
    finally:
        con.close()

    txt, csv_file, json_file = write_reports(rows)

    print("")
    print("ANWALTVORLAGE_GRUNDMODUL_V1 FERTIG")
    print("Fallvorlage:", CONFIG_DATA["case_template_key"])
    print("Vorlagen:", len(rows))
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
