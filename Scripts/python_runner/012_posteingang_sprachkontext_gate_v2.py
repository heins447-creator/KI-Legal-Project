# -*- coding: utf-8 -*-
import sys
import csv
import json
import hashlib
import argparse
import datetime
import re
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

DIRS = {
    "geprueft": POST / "02_Technisch_Geprueft",
    "vorzimmer": POST / "03_Vorzimmer_Entscheidung",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "protokolle": POST / "90_Protokolle",
    "sprachberichte": POST / "93_Sprachberichte"
}

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".eml", ".rtf", ".html", ".htm"
}

LANGUAGE_MARKERS = {
    "de": [
        "und", "der", "die", "das", "nicht", "mit", "gericht", "anwalt",
        "mandant", "schriftsatz", "beweis", "klage", "kündigung",
        "arbeitsrecht", "sprache", "verfahren", "gegenseite"
    ],
    "sv": [
        "och", "att", "är", "för", "till", "inte", "med", "som",
        "tingsrätt", "arbetsdomstolen", "förvaltningsrätten",
        "skadestånd", "anställning", "uppsägning", "skola",
        "mål", "svaranden", "käranden"
    ],
    "en": [
        "and", "the", "not", "with", "court", "lawyer", "client",
        "employment", "claim", "evidence", "language", "signed",
        "proceedings", "opponent", "document"
    ]
}

LANGUAGE_NAMES_DE = {
    "bg": "Bulgarisch",
    "hr": "Kroatisch",
    "cs": "Tschechisch",
    "da": "Dänisch",
    "nl": "Niederländisch",
    "en": "Englisch",
    "et": "Estnisch",
    "fi": "Finnisch",
    "fr": "Französisch",
    "de": "Deutsch",
    "el": "Griechisch",
    "hu": "Ungarisch",
    "ga": "Irisch",
    "it": "Italienisch",
    "lv": "Lettisch",
    "lt": "Litauisch",
    "mt": "Maltesisch",
    "pl": "Polnisch",
    "pt": "Portugiesisch",
    "ro": "Rumänisch",
    "sk": "Slowakisch",
    "sl": "Slowenisch",
    "es": "Spanisch",
    "sv": "Schwedisch",
    "unknown": "Unbekannt"
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
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

def read_text_sample(path):
    name_text = path.name

    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return name_text

    try:
        raw = path.read_bytes()[:300000]
    except Exception:
        return name_text

    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            return name_text + "\n" + raw.decode(enc, errors="replace")
        except Exception:
            pass

    return name_text

def score_language(text):
    low = text.lower()
    low = low.replace("_", " ").replace("-", " ")

    scores = {}

    for lang, words in LANGUAGE_MARKERS.items():
        score = 0
        for word in words:
            if " " in word:
                if word in low:
                    score += 2
            else:
                score += len(re.findall(r"(?<![a-zäöüåäöéèêáàíìóòúù])" + re.escape(word) + r"(?![a-zäöüåäöéèêáàíìóòúù])", low))
        scores[lang] = score

    best = max(scores, key=scores.get)
    ordered = sorted(scores.values(), reverse=True)

    if scores[best] == 0:
        return "unknown", scores, "Keine belastbaren Sprachmerkmale erkannt."

    if len(ordered) >= 2 and ordered[0] - ordered[1] < 2:
        return "unknown", scores, "Sprachmerkmale nicht eindeutig genug."

    return best, scores, "Sprache nach einfachen Textmerkmalen erkannt."

def load_language_context(case_template):
    con = duckdb.connect(str(DB), read_only=True)

    try:
        tables = {r[0] for r in con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchall()}

        required = {
            "lang_language_catalog",
            "lang_staff_language_settings",
            "lang_case_language_settings",
            "lang_participant_language_settings",
            "lang_intake_language_rules"
        }

        missing = sorted(required - tables)
        if missing:
            raise RuntimeError("Sprachkontext V2 fehlt oder ist unvollständig: " + ", ".join(missing))

        eu_count = con.execute("""
            SELECT COUNT(*)
            FROM lang_language_catalog
            WHERE eu_official = TRUE
        """).fetchone()[0]

        if eu_count != 24:
            raise RuntimeError("EU24-Sprachkatalog unvollständig: " + str(eu_count))

        case_row = con.execute("""
            SELECT case_template_key, case_label, jurisdiction_country_code, legal_area_key,
                   country_language_code, procedural_language_code, internal_work_language_code,
                   default_document_language_code, default_actual_language_code,
                   translation_required_default, interpreter_required_default
            FROM lang_case_language_settings
            WHERE case_template_key = ?
        """, [case_template]).fetchone()

        if case_row is None:
            raise RuntimeError("Fall-Sprachvorlage fehlt: " + case_template)

        participants = con.execute("""
            SELECT participant_profile_key, participant_role, participant_label,
                   official_or_procedural_language_code, communication_language_code,
                   document_language_code, actual_or_spoken_language_code,
                   fallback_language_code, translation_required,
                   created_after_mandate_acceptance, accepted_client_required
            FROM lang_participant_language_settings
            WHERE case_template_key = ?
            ORDER BY participant_role, participant_profile_key
        """, [case_template]).fetchall()

        return {
            "eu_count": eu_count,
            "case": {
                "case_template_key": case_row[0],
                "case_label": case_row[1],
                "jurisdiction_country_code": case_row[2],
                "legal_area_key": case_row[3],
                "country_language_code": case_row[4],
                "procedural_language_code": case_row[5],
                "internal_work_language_code": case_row[6],
                "default_document_language_code": case_row[7],
                "default_actual_language_code": case_row[8],
                "translation_required_default": bool(case_row[9]),
                "interpreter_required_default": bool(case_row[10])
            },
            "participants": [
                {
                    "participant_profile_key": r[0],
                    "participant_role": r[1],
                    "participant_label": r[2],
                    "official_or_procedural_language_code": r[3],
                    "communication_language_code": r[4],
                    "document_language_code": r[5],
                    "actual_or_spoken_language_code": r[6],
                    "fallback_language_code": r[7],
                    "translation_required": bool(r[8]),
                    "created_after_mandate_acceptance": bool(r[9]),
                    "accepted_client_required": bool(r[10])
                }
                for r in participants
            ]
        }

    finally:
        con.close()

def create_test_files():
    target = DIRS["geprueft"]
    target.mkdir(parents=True, exist_ok=True)

    samples = {
        "TEST_LANG_V2_001_deutsch.txt":
            "Dies ist ein deutscher Testtext. Der Anwalt arbeitet intern deutsch. Es geht um Sprache, Dokument und Kommunikation.\n",
        "TEST_LANG_V2_002_schwedisch.txt":
            "Detta är en svensk testtext. Målet gäller arbetsrätt och handlingen hör till en svensk process.\n",
        "TEST_LANG_V2_003_englisch.txt":
            "This is an English test document. Communication with the opposing lawyer may be in English.\n"
    }

    for name, content in samples.items():
        p = target / name
        if not p.exists():
            p.write_text(content, encoding="utf-8", newline="\n")

def classify_file(path, context):
    digest = sha256_file(path)
    intake_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + digest[:12]

    text = read_text_sample(path)
    detected, scores, detection_note = score_language(text)

    case = context["case"]

    expected_document_language = case["default_document_language_code"]
    procedural_language = case["procedural_language_code"]
    internal_language = case["internal_work_language_code"]

    if detected == "unknown":
        status = "SPRACHE_UNKLAR_VORZIMMER"
        translation_required = True
        decision = "Vorzimmer muß Sprache prüfen. Datei nicht automatisch in die normale Bearbeitung überführen."
    elif detected == expected_document_language:
        status = "SPRACHE_PASSEND"
        translation_required = case["translation_required_default"]
        decision = "Sprache paßt zur erwarteten Dokumentensprache. Weitergabe nach Vorzimmerentscheidung möglich."
    else:
        status = "SPRACHE_ABWEICHUNG_UEBERSETZUNG_PRUEFEN"
        translation_required = True
        decision = "Dokumentensprache weicht vom Fallprofil ab. Übersetzungsbedarf und richtige Kommunikationssprache prüfen."

    record = {
        "language_check_id": intake_id,
        "checked_at": now(),
        "source_path": str(path),
        "original_name": path.name,
        "sha256": digest,
        "case_template_key": case["case_template_key"],
        "case_label": case["case_label"],
        "jurisdiction_country_code": case["jurisdiction_country_code"],
        "legal_area_key": case["legal_area_key"],
        "expected_document_language_code": expected_document_language,
        "expected_document_language_de": LANGUAGE_NAMES_DE.get(expected_document_language, expected_document_language),
        "detected_actual_language_code": detected,
        "detected_actual_language_de": LANGUAGE_NAMES_DE.get(detected, detected),
        "procedural_language_code": procedural_language,
        "procedural_language_de": LANGUAGE_NAMES_DE.get(procedural_language, procedural_language),
        "internal_work_language_code": internal_language,
        "internal_work_language_de": LANGUAGE_NAMES_DE.get(internal_language, internal_language),
        "translation_required": translation_required,
        "interpreter_required": case["interpreter_required_default"],
        "language_status": status,
        "language_scores_json": json.dumps(scores, ensure_ascii=False),
        "detection_note": detection_note,
        "decision_recommendation": decision,
        "participant_language_context": context["participants"]
    }

    card = DIRS["sprachberichte"] / f"{intake_id}_sprachbericht.json"
    card.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    vorzimmer_card = DIRS["vorzimmer"] / f"{intake_id}_sprachkarte.json"
    vorzimmer_card.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    record["language_report"] = str(card)
    record["vorzimmer_language_card"] = str(vorzimmer_card)

    return record

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-template", default="TEMPLATE_SE_ARBEITSRECHT")
    parser.add_argument("--create-test", action="store_true")
    args = parser.parse_args()

    ensure_dirs()

    if args.create_test:
        create_test_files()

    context = load_language_context(args.case_template)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    protocol = DIRS["protokolle"] / f"POSTEINGANG_SPRACHKONTEXT_GATE_V2_{ts}.txt"
    csv_file = DIRS["protokolle"] / f"POSTEINGANG_SPRACHKONTEXT_GATE_V2_{ts}.csv"
    jsonl_file = DIRS["protokolle"] / f"POSTEINGANG_SPRACHKONTEXT_GATE_V2_{ts}.jsonl"

    candidates = sorted([
        p for p in DIRS["geprueft"].iterdir()
        if p.is_file() and p.name != ".gitkeep"
    ])

    records = []

    for file in candidates:
        try:
            records.append(classify_file(file, context))
        except Exception as exc:
            records.append({
                "language_check_id": "FEHLER",
                "checked_at": now(),
                "source_path": str(file),
                "original_name": file.name,
                "sha256": "",
                "case_template_key": args.case_template,
                "case_label": "",
                "jurisdiction_country_code": "",
                "legal_area_key": "",
                "expected_document_language_code": "",
                "expected_document_language_de": "",
                "detected_actual_language_code": "unknown",
                "detected_actual_language_de": "Unbekannt",
                "procedural_language_code": "",
                "procedural_language_de": "",
                "internal_work_language_code": "",
                "internal_work_language_de": "",
                "translation_required": True,
                "interpreter_required": False,
                "language_status": "FEHLER_BEI_SPRACHPRUEFUNG",
                "language_scores_json": "{}",
                "detection_note": repr(exc),
                "decision_recommendation": "Nicht weiterleiten. Fehler bei Sprachprüfung.",
                "language_report": "",
                "vorzimmer_language_card": ""
            })

    fields = [
        "language_check_id",
        "checked_at",
        "source_path",
        "original_name",
        "sha256",
        "case_template_key",
        "case_label",
        "jurisdiction_country_code",
        "legal_area_key",
        "expected_document_language_code",
        "expected_document_language_de",
        "detected_actual_language_code",
        "detected_actual_language_de",
        "procedural_language_code",
        "procedural_language_de",
        "internal_work_language_code",
        "internal_work_language_de",
        "translation_required",
        "interpreter_required",
        "language_status",
        "language_scores_json",
        "detection_note",
        "decision_recommendation",
        "language_report",
        "vorzimmer_language_card"
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fields})

    with open(jsonl_file, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(protocol, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG SPRACHKONTEXT GATE V2\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Fallvorlage: " + args.case_template + "\n")
        f.write("Verarbeitete Dateien: " + str(len(records)) + "\n\n")

        f.write("Fallkontext\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(context["case"], ensure_ascii=False, indent=2) + "\n\n")

        f.write("Beteiligtenkontext\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(context["participants"], ensure_ascii=False, indent=2) + "\n\n")

        f.write("Ergebnisse\n")
        f.write("-" * 80 + "\n")

        for r in records:
            f.write(
                f"{r.get('language_check_id')} | {r.get('original_name')} | "
                f"erwartet={r.get('expected_document_language_code')} | "
                f"erkannt={r.get('detected_actual_language_code')} | "
                f"{r.get('language_status')} | Übersetzung={r.get('translation_required')}\n"
            )

    print("")
    print("POSTEINGANG_SPRACHKONTEXT_GATE_V2 FERTIG")
    print("Fallvorlage:", args.case_template)
    print("Protokoll:", protocol)
    print("CSV:", csv_file)
    print("JSONL:", jsonl_file)
    print("Verarbeitete Dateien:", len(records))

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("")
        print("ABGEBROCHEN DURCH STRG+C")
        print("Zurück zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(130)
    except Exception as exc:
        print("")
        print("FEHLER")
        print(repr(exc))
        print("Zurück zum Einstiegspunkt: I:\\KI_Legal_Project")
        sys.exit(1)
