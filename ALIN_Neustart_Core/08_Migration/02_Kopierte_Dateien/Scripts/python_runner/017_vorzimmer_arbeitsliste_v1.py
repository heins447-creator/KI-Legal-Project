# -*- coding: utf-8 -*-
import sys
import csv
import json
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(r"I:\KI_Legal_Project")
POST = ROOT / "Posteingang"
OUT = ROOT / "Windows_App" / "Logs" / "Vorzimmer_Arbeitslisten"

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
}

WORK_KEYS = [
    "roh",
    "quarantaene",
    "signatur",
    "sprachpruefung",
    "rueckfrage",
    "vorzimmer",
    "geprueft",
    "anwalt",
    "abgewiesen",
]

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

PRIORITY = {
    "roh": 5,
    "quarantaene": 10,
    "signatur": 20,
    "sprachpruefung": 30,
    "rueckfrage": 40,
    "vorzimmer": 50,
    "geprueft": 60,
    "anwalt": 70,
    "abgewiesen": 90,
}

LABELS = {
    "roh": "Roh-Eingang offen",
    "quarantaene": "Quarantäne offen",
    "signatur": "Signaturprüfung offen",
    "sprachpruefung": "Sprachprüfung offen",
    "rueckfrage": "Rückfrage an Absender offen",
    "vorzimmer": "Vorzimmerentscheidung offen",
    "geprueft": "Technisch geprüft, noch nicht weitergeleitet",
    "anwalt": "Anwaltvorlage offen",
    "abgewiesen": "Abgewiesener Eingang vorhanden",
}

DECISIONS = {
    "roh": [
        "Produktionslauf starten",
        "Eingang zurückstellen",
    ],
    "quarantaene": [
        "Nicht öffnen",
        "technische Nachprüfung beauftragen",
        "Absender um Ersatzübersendung bitten",
        "Eingang zurückweisen",
    ],
    "signatur": [
        "Signaturprüfung beauftragen",
        "Absenderstatus prüfen",
        "Ersatzübersendung verlangen",
        "nicht in den normalen Bestand übernehmen",
    ],
    "sprachpruefung": [
        "Übersetzungsbedarf markieren",
        "Sprache manuell festlegen",
        "Vorlage an Anwalt vorbereiten",
        "Rückfrage an Absender",
    ],
    "rueckfrage": [
        "Rückfrage schreiben",
        "Ersatzdokument verlangen",
        "Frist vormerken",
        "zurückweisen",
    ],
    "vorzimmer": [
        "Anwaltvorlage",
        "Rückfrage an Absender",
        "Signaturprüfung",
        "Sprachprüfung",
        "Abweisung",
    ],
    "geprueft": [
        "Sprachprüfung starten",
        "Anwaltvorlage vorbereiten",
        "Aktenzuordnung vorbereiten",
        "Rückfrage an Absender",
    ],
    "anwalt": [
        "Anwalt vorlegen",
        "Frist prüfen",
        "Mandatsannahme prüfen",
        "Aktenanlage vorbereiten",
    ],
    "abgewiesen": [
        "Abweisung dokumentieren",
        "Archivieren",
        "keine weitere Bearbeitung",
    ],
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

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
    ]:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]

    if "__" in stem:
        return stem.split("__", 1)[0]

    parts = stem.split("_")
    if len(parts) >= 2 and parts[0].isdigit():
        return parts[0] + "_" + parts[1]

    return stem

def active_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def evidence_index():
    index = {}

    for key in ["sicherheit", "sprachen"]:
        for file in active_files(DIRS[key]):
            intake = extract_intake_id(file)
            index.setdefault(intake, []).append(str(file))

    return index

def summarize_json(data):
    fields = [
        "security_status",
        "language_status",
        "risk_level",
        "reason",
        "decision_recommendation",
        "original_name",
        "stored_path",
        "expected_document_language_code",
        "detected_actual_language_code",
        "translation_required",
    ]

    parts = []
    for f in fields:
        if f in data and data[f] not in (None, ""):
            parts.append(f + "=" + str(data[f]))

    return " | ".join(parts)

def build_entries():
    ensure_dirs()
    evidence = evidence_index()
    entries = []

    for key in WORK_KEYS:
        for file in active_files(DIRS[key]):
            intake = extract_intake_id(file)
            data = read_json(file) if file.suffix.lower() == ".json" else {}

            original_name = data.get("original_name") or file.name
            note = summarize_json(data)

            if not note:
                note = LABELS.get(key, key)

            entries.append({
                "priority": PRIORITY.get(key, 99),
                "bereich": key,
                "lage": LABELS.get(key, key),
                "intake_id": intake,
                "original_name": original_name,
                "source_path": str(file),
                "hinweis": note,
                "zulaessige_entscheidungen": " | ".join(DECISIONS.get(key, [])),
                "nachweise": " | ".join(evidence.get(intake, [])),
            })

    entries.sort(key=lambda x: (x["priority"], x["bereich"], x["original_name"]))
    return entries

def write_reports(entries):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"VORZIMMER_ARBEITSLISTE_V1_{ts}.txt"
    csv_file = OUT / f"VORZIMMER_ARBEITSLISTE_V1_{ts}.csv"
    json_file = OUT / f"VORZIMMER_ARBEITSLISTE_V1_{ts}.json"

    data = {
        "time": now(),
        "entries_count": len(entries),
        "entries": entries,
        "principle": "Die Liste bereitet Entscheidungen vor. Sie verschiebt keine Datei und trifft keine anwaltliche Entscheidung.",
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "priority",
        "bereich",
        "lage",
        "intake_id",
        "original_name",
        "source_path",
        "hinweis",
        "zulaessige_entscheidungen",
        "nachweise",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for row in entries:
            writer.writerow(row)

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("VORZIMMER ARBEITSLISTE V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Offene Entscheidungen: " + str(len(entries)) + "\n\n")

        if not entries:
            f.write("Keine offenen Vorzimmerentscheidungen gefunden.\n")
        else:
            for i, row in enumerate(entries, start=1):
                f.write("\n" + str(i) + ". " + row["lage"] + "\n")
                f.write("-" * 80 + "\n")
                f.write("Priorität: " + str(row["priority"]) + "\n")
                f.write("Bereich: " + row["bereich"] + "\n")
                f.write("Intake-ID: " + row["intake_id"] + "\n")
                f.write("Originalname: " + row["original_name"] + "\n")
                f.write("Quelle: " + row["source_path"] + "\n")
                f.write("Hinweis: " + row["hinweis"] + "\n")
                f.write("Zulässige Entscheidungen: " + row["zulaessige_entscheidungen"] + "\n")
                if row["nachweise"]:
                    f.write("Nachweise: " + row["nachweise"] + "\n")

    return txt, csv_file, json_file

def main():
    entries = build_entries()
    txt, csv_file, json_file = write_reports(entries)

    print("")
    print("VORZIMMER_ARBEITSLISTE_V1 FERTIG")
    print("Offene Entscheidungen:", len(entries))
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
