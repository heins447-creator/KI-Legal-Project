# -*- coding: utf-8 -*-
import sys
import json
import csv
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(r"I:\KI_Legal_Project")
POST = ROOT / "Posteingang"
LOG = ROOT / "Windows_App" / "Logs"
DB = ROOT / "Database" / "Legal_Brain.duckdb"
CONFIG = ROOT / "Config" / "posteingang_schlusskontrolle_v2.json"

OUT = LOG / "Posteingang_Schlusskontrolle"
TRANSLATION_DIR = POST / "96_Uebersetzung_DE"
FINAL_CARD_DIR = POST / "97_Schlusskontrolle"

DIRS = {
    "roh": POST / "00_Roh_Eingang",
    "quarantaene": POST / "01_Quarantaene",
    "geprueft": POST / "02_Technisch_Geprueft",
    "vorzimmer": POST / "03_Vorzimmer_Entscheidung",
    "anwalt": POST / "04_Anwaltvorlage",
    "rueckfrage": POST / "05_Rueckfrage_Absender",
    "abgewiesen": POST / "06_Abgewiesen",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "sicherheit": POST / "92_Sicherheitsberichte",
    "sprachen": POST / "93_Sprachberichte",
    "dokumentsprache": POST / "95_Dokumentsprachprofile",
}

WORK_AREAS = [
    "roh",
    "quarantaene",
    "geprueft",
    "vorzimmer",
    "anwalt",
    "rueckfrage",
    "abgewiesen",
    "signatur",
    "sprachpruefung",
]

EVIDENCE_AREAS = [
    "sicherheit",
    "sprachen",
    "dokumentsprache",
]

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

CONFIG_DATA = {
    "version": "V2",
    "required_final_points": [
        "sicher",
        "bearbeitet",
        "sprache_erkannt",
        "arbeitsuebersetzung_de_moeglich",
        "anwaltvorlage"
    ],
    "case_context": {
        "case_type": "Schwedischer Arbeitsrechtsstreit",
        "official_language": "sv",
        "procedural_language": "sv",
        "internal_work_language": "de",
        "rough_translation_target": "de"
    },
    "translation_backend": {
        "status": "vorbereitet",
        "allowed_backends": ["google", "ki", "lokales_sprachmodell"],
        "note": "Der Posteingang erzeugt Übersetzungsaufträge. Die konkrete Google- oder KI-Übersetzung kann daran angeschlossen werden."
    },
    "principle": "Die Schlußkontrolle entscheidet nicht über Beweiswert, Entlastung, rechtliche Erheblichkeit oder Aktenzuordnung. Sie stellt nur fest, ob der Eingang sicher, technisch bearbeitet, sprachlich vorerfaßt, übersetzbar und für die Anwaltvorlage bereit oder vorbereitbar ist."
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    TRANSLATION_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_CARD_DIR.mkdir(parents=True, exist_ok=True)

    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    for p in [TRANSLATION_DIR, FINAL_CARD_DIR]:
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

def active_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def extract_intake_id(path):
    stem = path.stem

    for suffix in [
        "_entscheidungskarte",
        "_sicherheitskarte",
        "_sprachkarte",
        "_sicherheitsbericht",
        "_sprachbericht",
        "_dokumentsprachprofil",
        "_schlusskarte",
    ]:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]

    if "__" in stem:
        return stem.split("__", 1)[0]

    parts = stem.split("_")
    if len(parts) >= 2 and parts[0].isdigit():
        return parts[0] + "_" + parts[1]

    return stem

def all_relevant_files():
    result = []

    for area in WORK_AREAS + EVIDENCE_AREAS:
        for file in active_files(DIRS[area]):
            result.append({
                "area": area,
                "path": file,
                "intake_id": extract_intake_id(file),
                "json": read_json(file) if file.suffix.lower() == ".json" else {},
            })

    return result

def load_db_language_profiles():
    profiles = {}

    if not DB.exists():
        return profiles

    try:
        import duckdb
    except Exception:
        return profiles

    con = None
    try:
        con = duckdb.connect(str(DB), read_only=True)

        tables = [
            x[0] for x in con.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                ORDER BY table_name
            """).fetchall()
        ]

        if "posteingang_document_language_profile" not in tables:
            return profiles

        info = con.execute("PRAGMA table_info(posteingang_document_language_profile)").fetchall()
        cols = [str(x[1]) for x in info]
        rows = con.execute("SELECT * FROM posteingang_document_language_profile").fetchall()

        for row in rows:
            data = dict(zip(cols, row))

            key = ""
            for candidate in ["intake_id", "document_id", "document_key", "file_id"]:
                if candidate in data and data[candidate]:
                    key = str(data[candidate])
                    break

            if not key:
                for value in data.values():
                    if value and isinstance(value, str) and "_" in value:
                        key = value
                        break

            if key:
                profiles[key] = data

    except Exception:
        return profiles
    finally:
        if con is not None:
            con.close()

    return profiles

def first_value(data, keys):
    for key in keys:
        if key in data and data[key] not in ("", None):
            return data[key]
    return ""

def collect_by_intake(files):
    grouped = {}

    for item in files:
        grouped.setdefault(item["intake_id"], []).append(item)

    return grouped

def derive_original_name(items, profile):
    for item in items:
        data = item.get("json") or {}
        value = first_value(data, ["original_name", "filename", "source_name"])
        if value:
            return str(value)

    value = first_value(profile, ["original_name", "filename", "source_name", "document_name"])
    if value:
        return str(value)

    for item in items:
        if item["area"] in WORK_AREAS:
            return item["path"].name

    return items[0]["path"].name if items else ""

def derive_language(items, profile):
    candidates = []

    for data in [profile]:
        if data:
            candidates.append(first_value(data, [
                "primary_language_code",
                "detected_primary_language_code",
                "detected_actual_language_code",
                "actual_language_code",
                "language_code",
                "document_language_code",
            ]))

    for item in items:
        data = item.get("json") or {}
        candidates.append(first_value(data, [
            "primary_language_code",
            "detected_primary_language_code",
            "detected_actual_language_code",
            "actual_language_code",
            "language_code",
            "document_language_code",
        ]))

    primary = ""
    for c in candidates:
        if c and str(c).lower() not in {"unknown", "unklar", "none"}:
            primary = str(c).lower()
            break

    if not primary:
        primary = "unknown"

    extra = []

    for data in [profile] + [item.get("json") or {} for item in items]:
        for key in [
            "detected_languages_json",
            "all_languages_json",
            "secondary_languages_json",
            "languages_json",
        ]:
            value = data.get(key) if isinstance(data, dict) else None
            if value:
                try:
                    if isinstance(value, str):
                        parsed = json.loads(value)
                    else:
                        parsed = value
                    if isinstance(parsed, list):
                        for x in parsed:
                            sx = str(x).lower()
                            if sx and sx not in extra:
                                extra.append(sx)
                except Exception:
                    pass

    if primary != "unknown" and primary not in extra:
        extra.insert(0, primary)

    is_multilingual = len([x for x in extra if x and x != "unknown"]) > 1

    return primary, extra, is_multilingual

def derive_security(items):
    areas = {item["area"] for item in items}

    if "quarantaene" in areas:
        return "NICHT_SICHER_QUARANTAENE", False

    if "signatur" in areas:
        return "SIGNATURPRUEFUNG_OFFEN", False

    for item in items:
        data = item.get("json") or {}
        status = str(first_value(data, ["security_status", "status", "posteingang_status"])).upper()
        if "GESPERRT" in status or "QUARANTAENE" in status:
            return status, False
        if "SIGNATUR" in status and "ERFORDERLICH" in status:
            return status, False

    for item in items:
        data = item.get("json") or {}
        status = str(first_value(data, ["security_status", "status", "posteingang_status"])).upper()
        if "FREIGEGEBEN" in status or "GEPRUEFT" in status or "SICHERHEIT" in status:
            return status, True

    if "geprueft" in areas or "vorzimmer" in areas or "anwalt" in areas:
        return "SICHERHEIT_NACH_PIPELINE_PLAUSIBEL", True

    return "SICHERHEIT_UNKLAR", False

def derive_processed(items, profile):
    areas = {item["area"] for item in items}

    if "roh" in areas:
        return False, "ROH_EINGANG_NOCH_NICHT_BEARBEITET"

    if profile:
        return True, "DOKUMENTSPRACHPROFIL_VORHANDEN"

    for item in items:
        if item["area"] in EVIDENCE_AREAS:
            return True, "NACHWEIS_VORHANDEN"

    if areas:
        return True, "PIPELINEBEREICH_VORHANDEN"

    return False, "NICHT_BEARBEITET"

def create_translation_job(intake_id, original_name, primary_language, extra_languages, items):
    if primary_language in {"", "unknown", "de"}:
        return "", "NICHT_ERFORDERLICH_ODER_SPRACHE_UNKLAR"

    source_paths = [
        str(item["path"]) for item in items
        if item["area"] in WORK_AREAS
        and item["path"].suffix.lower() != ".json"
    ]

    job = {
        "time": now(),
        "intake_id": intake_id,
        "original_name": original_name,
        "source_language_primary": primary_language,
        "source_languages_all": extra_languages,
        "target_language": "de",
        "translation_level": "grobe Arbeitsübersetzung für Anwaltvorlage",
        "backend_policy": CONFIG_DATA["translation_backend"],
        "source_paths": source_paths,
        "status": "UEBERSETZUNGSAUFTRAG_ANGELEGT",
        "note": "Dies ist noch keine fachliche Übersetzung. Der Posteingang stellt nur die automatische Kurz- oder Arbeitsübersetzung nach Deutsch bereit beziehungsweise stößt sie an."
    }

    target = TRANSLATION_DIR / f"{intake_id}_uebersetzung_de_job.json"
    target.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return str(target), "UEBERSETZUNG_DE_AUFTRAG_ANGELEGT"

def derive_lawyer_status(items, security_ok, language_ok, translation_status):
    areas = {item["area"] for item in items}

    if "anwalt" in areas:
        return "ANWALTVORLAGE_BEREIT"

    if "quarantaene" in areas:
        return "NICHT_BEREIT_TECHNISCHE_QUARANTAENE"

    if "signatur" in areas:
        return "NICHT_BEREIT_SIGNATURPRUEFUNG_OFFEN"

    if "roh" in areas:
        return "NICHT_BEREIT_ROHEINGANG"

    if not security_ok:
        return "NICHT_BEREIT_SICHERHEIT_UNKLAR"

    if not language_ok:
        return "NICHT_BEREIT_SPRACHE_UNKLAR"

    if "geprueft" in areas or "vorzimmer" in areas:
        return "VORBEREITBAR_DURCH_VORZIMMER"

    return "NICHT_BEREIT_ZUSTAND_UNKLAR"

def build_records():
    ensure_dirs()

    files = all_relevant_files()
    grouped = collect_by_intake(files)
    db_profiles = load_db_language_profiles()

    intake_ids = set(grouped.keys())

    for key in db_profiles.keys():
        intake_ids.add(key)

    records = []

    for intake_id in sorted(intake_ids):
        items = grouped.get(intake_id, [])

        profile = db_profiles.get(intake_id, {})

        if not profile:
            for key, value in db_profiles.items():
                if intake_id in key or key in intake_id:
                    profile = value
                    break

        original_name = derive_original_name(items, profile)
        primary_language, all_languages, multilingual = derive_language(items, profile)
        language_ok = primary_language not in {"", "unknown"}

        security_status, security_ok = derive_security(items)
        processed, processed_status = derive_processed(items, profile)

        translation_job, translation_status = create_translation_job(
            intake_id,
            original_name,
            primary_language,
            all_languages,
            items
        )

        if primary_language == "de":
            rough_translation_possible = True
            translation_status = "DEUTSCH_BEREITS_ARBEITSSPRACHE"
        elif language_ok:
            rough_translation_possible = True
        else:
            rough_translation_possible = False

        lawyer_status = derive_lawyer_status(items, security_ok, language_ok, translation_status)

        final_ok = (
            security_ok
            and processed
            and language_ok
            and rough_translation_possible
            and lawyer_status in {"ANWALTVORLAGE_BEREIT", "VORBEREITBAR_DURCH_VORZIMMER"}
        )

        if final_ok:
            final_status = "SCHLUSSKONTROLLE_OK"
        elif not security_ok:
            final_status = "OFFEN_SICHERHEIT"
        elif not processed:
            final_status = "OFFEN_BEARBEITUNG"
        elif not language_ok:
            final_status = "OFFEN_SPRACHERKENNUNG"
        elif not rough_translation_possible:
            final_status = "OFFEN_UEBERSETZBARKEIT"
        else:
            final_status = "OFFEN_ANWALTVORLAGE_ODER_VORZIMMER"

        current_areas = sorted({item["area"] for item in items})

        source_paths = [
            str(item["path"]) for item in items
            if item["area"] in WORK_AREAS
        ]

        evidence_paths = [
            str(item["path"]) for item in items
            if item["area"] in EVIDENCE_AREAS
        ]

        record = {
            "time": now(),
            "intake_id": intake_id,
            "original_name": original_name,
            "current_areas": current_areas,
            "security_status": security_status,
            "security_ok": security_ok,
            "processed_status": processed_status,
            "processed": processed,
            "primary_language_code": primary_language,
            "all_language_codes": all_languages,
            "is_multilingual": multilingual,
            "language_recognized": language_ok,
            "internal_work_language_code": "de",
            "rough_translation_target_language_code": "de",
            "rough_translation_possible": rough_translation_possible,
            "translation_status": translation_status,
            "translation_job": translation_job,
            "lawyer_template_status": lawyer_status,
            "final_status": final_status,
            "source_paths": source_paths,
            "evidence_paths": evidence_paths,
            "posteingang_boundary": "Keine inhaltliche Beweis-, Entlastungs- oder Rechtsbewertung im Posteingang.",
        }

        card = FINAL_CARD_DIR / f"{intake_id}_schlusskarte.json"
        card.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        record["schlusskarte"] = str(card)

        records.append(record)

    return records

def write_reports(records):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"POSTEINGANG_SCHLUSSKONTROLLE_V2_{ts}.txt"
    csv_file = OUT / f"POSTEINGANG_SCHLUSSKONTROLLE_V2_{ts}.csv"
    json_file = OUT / f"POSTEINGANG_SCHLUSSKONTROLLE_V2_{ts}.json"

    summary = {
        "time": now(),
        "records_count": len(records),
        "ok_count": len([r for r in records if r["final_status"] == "SCHLUSSKONTROLLE_OK"]),
        "security_open_count": len([r for r in records if r["final_status"] == "OFFEN_SICHERHEIT"]),
        "language_open_count": len([r for r in records if r["final_status"] == "OFFEN_SPRACHERKENNUNG"]),
        "translation_jobs_count": len([r for r in records if r.get("translation_job")]),
        "lawyer_ready_or_preparable_count": len([
            r for r in records
            if r["lawyer_template_status"] in {"ANWALTVORLAGE_BEREIT", "VORBEREITBAR_DURCH_VORZIMMER"}
        ]),
        "records": records,
    }

    json_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "intake_id",
        "original_name",
        "security_ok",
        "processed",
        "language_recognized",
        "primary_language_code",
        "is_multilingual",
        "rough_translation_possible",
        "translation_status",
        "lawyer_template_status",
        "final_status",
        "translation_job",
        "schlusskarte",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for row in records:
            writer.writerow({k: row.get(k, "") for k in fields})

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG SCHLUSSKONTROLLE V2\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + summary["time"] + "\n")
        f.write("Datensätze: " + str(summary["records_count"]) + "\n")
        f.write("OK: " + str(summary["ok_count"]) + "\n")
        f.write("Sicherheit offen: " + str(summary["security_open_count"]) + "\n")
        f.write("Sprache offen: " + str(summary["language_open_count"]) + "\n")
        f.write("Übersetzungsaufträge Deutsch: " + str(summary["translation_jobs_count"]) + "\n")
        f.write("Anwaltvorlage bereit oder vorbereitbar: " + str(summary["lawyer_ready_or_preparable_count"]) + "\n\n")

        f.write("PRUEFPUNKTE\n")
        f.write("-" * 80 + "\n")
        f.write("1. sicher\n")
        f.write("2. bearbeitet\n")
        f.write("3. Sprache erkannt\n")
        f.write("4. grobe Arbeitsübersetzung nach Deutsch möglich\n")
        f.write("5. Anwaltvorlage bereit oder organisatorisch vorbereitbar\n\n")

        if not records:
            f.write("Keine aktiven oder nachweisbaren Eingänge gefunden.\n")
        else:
            for i, r in enumerate(records, start=1):
                f.write(str(i) + ". " + r["final_status"] + "\n")
                f.write("-" * 80 + "\n")
                f.write("Intake-ID: " + r["intake_id"] + "\n")
                f.write("Name: " + r["original_name"] + "\n")
                f.write("Bereiche: " + ", ".join(r["current_areas"]) + "\n")
                f.write("Sicher: " + str(r["security_ok"]) + " | " + r["security_status"] + "\n")
                f.write("Bearbeitet: " + str(r["processed"]) + " | " + r["processed_status"] + "\n")
                f.write("Sprache erkannt: " + str(r["language_recognized"]) + " | " + r["primary_language_code"] + "\n")
                f.write("Mehrsprachig: " + str(r["is_multilingual"]) + " | " + json.dumps(r["all_language_codes"], ensure_ascii=False) + "\n")
                f.write("Arbeitsübersetzung DE möglich: " + str(r["rough_translation_possible"]) + " | " + r["translation_status"] + "\n")
                if r["translation_job"]:
                    f.write("Übersetzungsauftrag: " + r["translation_job"] + "\n")
                f.write("Anwaltvorlage: " + r["lawyer_template_status"] + "\n")
                f.write("Schlußkarte: " + r["schlusskarte"] + "\n\n")

    return summary, txt, csv_file, json_file

def main():
    records = build_records()
    summary, txt, csv_file, json_file = write_reports(records)

    print("")
    print("POSTEINGANG_SCHLUSSKONTROLLE_V2 FERTIG")
    print("Datensätze:", summary["records_count"])
    print("OK:", summary["ok_count"])
    print("Sicherheit offen:", summary["security_open_count"])
    print("Sprache offen:", summary["language_open_count"])
    print("Übersetzungsaufträge Deutsch:", summary["translation_jobs_count"])
    print("Anwaltvorlage bereit oder vorbereitbar:", summary["lawyer_ready_or_preparable_count"])
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", json_file)

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
