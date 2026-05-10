# -*- coding: utf-8 -*-
import sys
import csv
import json
import hashlib
import uuid
import re
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
OUT = LOG / "Dokumentsprachprofile"
CONFIG = ROOT / "Config" / "dokumentsprachprofil_v1.json"

DIRS = {
    "roh": POST / "00_Roh_Eingang",
    "geprueft": POST / "02_Technisch_Geprueft",
    "vorzimmer": POST / "03_Vorzimmer_Entscheidung",
    "anwalt": POST / "04_Anwaltvorlage",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "profile": POST / "95_Dokumentsprachprofile",
}

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

TEXT_EXT = {".txt", ".md", ".csv", ".json", ".xml", ".eml"}
BINARY_SAFE_NAME_ONLY = {".pdf", ".docx", ".xlsx", ".pptx", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".msg"}

CONFIG_DATA = {
    "version": "V1",
    "default_case_key": "TEMPLATE_SE_ARBEITSRECHT",
    "official_language_code": "sv",
    "procedural_language_code": "sv",
    "internal_work_language_code": "de",
    "rough_translation_target_language_code": "de",
    "document_language_id_rule": "DLANG_<sha256[:16]>",
    "language_routing_key_rule": "case|intake|primary|secondary|target",
    "principle": "Die Sprache läuft als Dokument-Sprachprofil mit. Mehrsprachige Dokumente werden markiert. Inhaltliche Beweis- oder Entlastungsbewertung erfolgt nicht im Posteingang."
}

LANGUAGE_MARKERS = {
    "sv": [
        "och", "att", "det", "som", "inte", "för", "med", "till", "från",
        "arbetsgivare", "arbetstagare", "arbetsrätt", "tingsrätt", "domstol",
        "mål nr", "skolan", "anmälan", "arbetsmiljö", "kommun", "lärare",
        "skolinspektionen", "kränkningar", "uppsägning"
    ],
    "de": [
        "und", "der", "die", "das", "nicht", "mit", "von", "gericht",
        "anwalt", "arbeitnehmer", "arbeitgeber", "arbeitsrecht", "schriftsatz",
        "anlage", "beweis", "entlastung", "aussage", "kündigung", "kommunal"
    ],
    "en": [
        "and", "the", "not", "with", "from", "court", "lawyer", "employee",
        "employer", "employment", "evidence", "statement", "attachment",
        "termination", "municipal", "school"
    ],
    "fr": ["et", "le", "la", "les", "tribunal", "avocat", "preuve", "employeur", "salarié"],
    "es": ["y", "el", "la", "los", "tribunal", "abogado", "prueba", "empleador", "trabajador"],
    "it": ["e", "il", "la", "tribunale", "avvocato", "prova", "datore", "lavoratore"],
    "nl": ["en", "de", "het", "rechtbank", "advocaat", "bewijs", "werkgever", "werknemer"],
    "da": ["og", "det", "ikke", "domstol", "advokat", "bevis", "arbejdsgiver"],
    "fi": ["ja", "että", "ei", "tuomioistuin", "asianajaja", "todiste", "työnantaja"],
    "pl": ["i", "nie", "sąd", "adwokat", "dowód", "pracodawca", "pracownik"],
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def normalize(text):
    text = text.lower()
    replacements = {
        "å": "å",
        "ä": "ä",
        "ö": "ö",
        "ü": "ü",
        "ß": "ss",
        "é": "e",
        "è": "e",
        "á": "a",
        "à": "a",
        "ó": "o",
        "ò": "o",
        "í": "i",
        "ú": "u",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    return text

def read_text_hint(path):
    pieces = [path.name]
    ext = path.suffix.lower()

    if ext in TEXT_EXT:
        try:
            data = path.read_bytes()[:128 * 1024]
            pieces.append(data.decode("utf-8", errors="replace"))
        except Exception:
            pass

    return "\n".join(pieces)

def language_scores(text):
    t = normalize(text)
    scores = {}

    for lang, markers in LANGUAGE_MARKERS.items():
        score = 0
        for marker in markers:
            m = normalize(marker)
            if " " in m:
                if m in t:
                    score += 4
            else:
                score += len(re.findall(r"\b" + re.escape(m) + r"\b", t))
        if score:
            scores[lang] = score

    return scores

def detect_languages(text):
    scores = language_scores(text)

    if not scores:
        return {
            "primary": "unknown",
            "all": [],
            "secondary": [],
            "scores": {},
            "is_multilingual": False,
            "confidence": "unklar",
        }

    ordered = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    primary = ordered[0][0]
    primary_score = ordered[0][1]

    detected = []
    for lang, score in ordered:
        if score >= 2 and (score >= max(2, primary_score * 0.20) or lang == primary):
            detected.append(lang)

    if primary not in detected:
        detected.insert(0, primary)

    secondary = [x for x in detected if x != primary]

    if primary_score >= 12:
        conf = "hoch"
    elif primary_score >= 5:
        conf = "mittel"
    else:
        conf = "niedrig"

    if len(detected) >= 2:
        conf = conf + "_mehrsprachig"

    return {
        "primary": primary,
        "all": detected,
        "secondary": secondary,
        "scores": scores,
        "is_multilingual": len(detected) >= 2,
        "confidence": conf,
    }

def extract_intake_id(path):
    stem = path.stem

    for suffix in [
        "_entscheidungskarte",
        "_sicherheitskarte",
        "_sprachkarte",
        "_sicherheitsbericht",
        "_sprachbericht",
        "_datenannahme_grundparameter",
        "_dokumentsprachprofil",
    ]:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]

    if "__" in stem:
        return stem.split("__", 1)[0]

    parts = stem.split("_")
    if len(parts) >= 2 and parts[0].isdigit():
        return parts[0] + "_" + parts[1]

    return stem

def source_files():
    result = []

    for area in ["roh", "geprueft", "anwalt", "signatur", "sprachpruefung"]:
        folder = DIRS[area]
        if not folder.exists():
            continue

        for p in folder.rglob("*"):
            if not p.is_file():
                continue
            if p.name in IGNORE:
                continue
            if p.suffix.lower() == ".json" and area in {"signatur", "sprachpruefung"}:
                continue
            result.append((area, p))

    return sorted(result, key=lambda x: str(x[1]).lower())

def make_record(area, path):
    digest = sha256_file(path)
    text_hint = read_text_hint(path)
    detected = detect_languages(text_hint)

    intake_id = extract_intake_id(path)
    document_language_id = "DLANG_" + digest[:16]
    primary = detected["primary"]
    all_langs = detected["all"]
    secondary = detected["secondary"]

    rough_required = True
    if primary == "de" and not secondary:
        rough_required = False

    language_routing_key = "|".join([
        CONFIG_DATA["default_case_key"],
        intake_id,
        primary,
        "+".join(secondary),
        CONFIG_DATA["rough_translation_target_language_code"],
    ])

    status = "SPRACHE_ERKANNT"
    if primary == "unknown":
        status = "SPRACHE_UNKLAR"
    elif detected["is_multilingual"]:
        status = "MEHRSPRACHIG_ERKANNT"

    basis = "Dateiname"
    if path.suffix.lower() in TEXT_EXT:
        basis = "Dateiname und lesbarer Textauszug"
    elif path.suffix.lower() in BINARY_SAFE_NAME_ONLY:
        basis = "Dateiname; Inhaltserkennung später durch OCR oder Fachagent"

    return {
        "document_language_id": document_language_id,
        "intake_id": intake_id,
        "document_key": digest[:24],
        "mandant_key": "",
        "case_key": CONFIG_DATA["default_case_key"],
        "source_area": area,
        "source_path": str(path),
        "original_name": path.name,
        "detected_primary_language_code": primary,
        "detected_language_codes_json": json.dumps(all_langs, ensure_ascii=False),
        "detected_secondary_language_codes_json": json.dumps(secondary, ensure_ascii=False),
        "is_multilingual": detected["is_multilingual"],
        "internal_work_language_code": CONFIG_DATA["internal_work_language_code"],
        "rough_translation_target_language_code": CONFIG_DATA["rough_translation_target_language_code"],
        "rough_translation_required": rough_required,
        "procedural_language_code": CONFIG_DATA["procedural_language_code"],
        "official_language_code": CONFIG_DATA["official_language_code"],
        "language_routing_key": language_routing_key,
        "confidence": detected["confidence"],
        "detection_basis": basis + "; scores=" + json.dumps(detected["scores"], ensure_ascii=False),
        "status": status,
        "created_at": now(),
        "updated_at": now(),
    }

def ensure_schema(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS posteingang_document_language_profile (
            document_language_id VARCHAR PRIMARY KEY,
            intake_id VARCHAR,
            document_key VARCHAR,
            mandant_key VARCHAR,
            case_key VARCHAR,
            source_area VARCHAR,
            source_path VARCHAR,
            original_name VARCHAR,
            detected_primary_language_code VARCHAR,
            detected_language_codes_json VARCHAR,
            detected_secondary_language_codes_json VARCHAR,
            is_multilingual BOOLEAN,
            internal_work_language_code VARCHAR,
            rough_translation_target_language_code VARCHAR,
            rough_translation_required BOOLEAN,
            procedural_language_code VARCHAR,
            official_language_code VARCHAR,
            language_routing_key VARCHAR,
            confidence VARCHAR,
            detection_basis VARCHAR,
            status VARCHAR,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS posteingang_document_language_audit (
            audit_id VARCHAR PRIMARY KEY,
            audit_time TIMESTAMP,
            document_language_id VARCHAR,
            intake_id VARCHAR,
            audit_status VARCHAR,
            details VARCHAR
        )
    """)

def write_profile_json(rec):
    target = DIRS["profile"] / (rec["document_language_id"] + "_dokumentsprachprofil.json")
    target.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    rec["profile_json"] = str(target)

def upsert_records(con, records):
    fields = [
        "document_language_id",
        "intake_id",
        "document_key",
        "mandant_key",
        "case_key",
        "source_area",
        "source_path",
        "original_name",
        "detected_primary_language_code",
        "detected_language_codes_json",
        "detected_secondary_language_codes_json",
        "is_multilingual",
        "internal_work_language_code",
        "rough_translation_target_language_code",
        "rough_translation_required",
        "procedural_language_code",
        "official_language_code",
        "language_routing_key",
        "confidence",
        "detection_basis",
        "status",
        "created_at",
        "updated_at",
    ]

    for r in records:
        con.execute(
            "DELETE FROM posteingang_document_language_profile WHERE document_language_id = ?",
            [r["document_language_id"]]
        )

        placeholders = ",".join(["?"] * len(fields))
        con.execute(
            "INSERT INTO posteingang_document_language_profile (" + ",".join(fields) + ") VALUES (" + placeholders + ")",
            [r.get(f, "") for f in fields]
        )

        con.execute(
            """
            INSERT INTO posteingang_document_language_audit
            (audit_id, audit_time, document_language_id, intake_id, audit_status, details)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """,
            [
                str(uuid.uuid4()),
                r["document_language_id"],
                r["intake_id"],
                r["status"],
                json.dumps({
                    "primary": r["detected_primary_language_code"],
                    "all": r["detected_language_codes_json"],
                    "source": r["source_path"],
                    "routing": r["language_routing_key"],
                }, ensure_ascii=False)
            ]
        )

def write_summary(records):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    txt = OUT / f"DOKUMENTSPRACHPROFIL_V1_{ts}.txt"
    csv_file = OUT / f"DOKUMENTSPRACHPROFIL_V1_{ts}.csv"
    jsonl = OUT / f"DOKUMENTSPRACHPROFIL_V1_{ts}.jsonl"

    fields = [
        "document_language_id",
        "intake_id",
        "document_key",
        "mandant_key",
        "case_key",
        "source_area",
        "original_name",
        "detected_primary_language_code",
        "detected_language_codes_json",
        "detected_secondary_language_codes_json",
        "is_multilingual",
        "internal_work_language_code",
        "rough_translation_target_language_code",
        "rough_translation_required",
        "procedural_language_code",
        "official_language_code",
        "language_routing_key",
        "confidence",
        "status",
        "source_path",
        "profile_json",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fields})

    with open(jsonl, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("DOKUMENTSPRACHPROFIL V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Datensätze: " + str(len(records)) + "\n\n")

        if not records:
            f.write("Keine aktiven Dokumente für Dokument-Sprachprofil gefunden.\n")
        else:
            for r in records:
                f.write(r["document_language_id"] + "\n")
                f.write("Intake-ID: " + r["intake_id"] + "\n")
                f.write("Dokument: " + r["original_name"] + "\n")
                f.write("Primärsprache: " + r["detected_primary_language_code"] + "\n")
                f.write("Alle Sprachen: " + r["detected_language_codes_json"] + "\n")
                f.write("Mehrsprachig: " + str(r["is_multilingual"]) + "\n")
                f.write("Übersetzung nach Deutsch erforderlich: " + str(r["rough_translation_required"]) + "\n")
                f.write("Routing: " + r["language_routing_key"] + "\n")
                f.write("Profil: " + r.get("profile_json", "") + "\n\n")

    return txt, csv_file, jsonl

def verify(con):
    count = con.execute("SELECT COUNT(*) FROM posteingang_document_language_profile").fetchone()[0]
    return count

def main():
    ensure_dirs()

    records = []
    for area, path in source_files():
        rec = make_record(area, path)
        write_profile_json(rec)
        records.append(rec)

    con = duckdb.connect(str(DB))
    try:
        ensure_schema(con)
        upsert_records(con, records)
        total = verify(con)
    finally:
        con.close()

    txt, csv_file, jsonl = write_summary(records)

    print("")
    print("DOKUMENTSPRACHPROFIL_V1 FERTIG")
    print("Aktuell erkannte Dokumente:", len(records))
    print("Dokumentsprachprofile in Datenbank:", total)
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSONL:", jsonl)
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
