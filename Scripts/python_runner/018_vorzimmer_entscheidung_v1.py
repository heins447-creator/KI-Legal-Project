# -*- coding: utf-8 -*-
import sys
import csv
import json
import shutil
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
DECISION_DIR = LOG / "Vorzimmer_Entscheidungen"
INPUT_DIR = DECISION_DIR
REPORT_DIR = DECISION_DIR / "Berichte"
PROCESSED_DIR = DECISION_DIR / "Verarbeitet"
FAILED_DIR = DECISION_DIR / "Fehler"
PROOF_DIR = DECISION_DIR / "Nachweise"
CONFIG_TEMPLATE = ROOT / "Config" / "vorzimmer_entscheidung_template_v1.csv"

INPUT_PREFIX = "EINGABE_VORZIMMER_ENTSCHEIDUNG_"

DIRS = {
    "quarantaene": POST / "01_Quarantaene",
    "geprueft": POST / "02_Technisch_Geprueft",
    "vorzimmer": POST / "03_Vorzimmer_Entscheidung",
    "anwalt": POST / "04_Anwaltvorlage",
    "rueckfrage": POST / "05_Rueckfrage_Absender",
    "abgewiesen": POST / "06_Abgewiesen",
    "signatur": POST / "07_Signaturpruefung",
    "sprachpruefung": POST / "08_Sprachpruefung",
    "archiv": POST / "99_Archiv_Altlasten",
}

WORK_DIRS = [
    DIRS["quarantaene"],
    DIRS["geprueft"],
    DIRS["vorzimmer"],
    DIRS["anwalt"],
    DIRS["rueckfrage"],
    DIRS["abgewiesen"],
    DIRS["signatur"],
    DIRS["sprachpruefung"],
]

ACTION_TARGETS = {
    "ANWALTVORLAGE": DIRS["anwalt"],
    "RUECKFRAGE_ABSENDER": DIRS["rueckfrage"],
    "ABWEISEN": DIRS["abgewiesen"],
    "SIGNATURPRUEFUNG": DIRS["signatur"],
    "SPRACHPRUEFUNG": DIRS["sprachpruefung"],
    "QUARANTAENE": DIRS["quarantaene"],
}

NO_MOVE_ACTIONS = {
    "KEINE_AKTION",
    "ZURUECKSTELLEN",
}

VALID_ACTIONS = set(ACTION_TARGETS.keys()) | NO_MOVE_ACTIONS | {"ARCHIVIEREN"}
IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    for p in list(DIRS.values()) + [INPUT_DIR, REPORT_DIR, PROCESSED_DIR, FAILED_DIR, PROOF_DIR]:
        p.mkdir(parents=True, exist_ok=True)

def write_template():
    CONFIG_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    text = (
        "decision_id;intake_id;source_path;aktion;begruendung;frist;verantwortlich\n"
        "BEISPIEL_NICHT_AUSFUEHREN;INTAKE_ID_AUS_ARBEITSLISTE;;ANWALTVORLAGE;Kurze Begründung der Vorzimmerentscheidung;;Vorzimmer\n"
    )

    CONFIG_TEMPLATE.write_text(text, encoding="utf-8", newline="\n")
    (INPUT_DIR / "EINGABE_VORZIMMER_ENTSCHEIDUNG_TEMPLATE.csv").write_text(text, encoding="utf-8", newline="\n")

def normalize_action(value):
    v = str(value or "").strip().upper()
    v = v.replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE").replace("ß", "SS")
    v = v.replace("-", "_").replace(" ", "_")
    return v

def active_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def decision_csv_files():
    files = []
    for p in INPUT_DIR.glob(INPUT_PREFIX + "*.csv"):
        name = p.name.upper()
        if "TEMPLATE" in name:
            continue
        files.append(p)
    return sorted(files)

def safe_unique(target):
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    parent = target.parent

    for i in range(1, 10000):
        candidate = parent / f"{stem}__{i:04d}{suffix}"
        if not candidate.exists():
            return candidate

    raise RuntimeError("Kein eindeutiger Zielname möglich: " + str(target))

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

def matching_files(intake_id, source_path):
    found = []

    if source_path:
        p = Path(source_path)
        if p.exists() and p.is_file():
            found.append(p)

    if intake_id:
        for folder in WORK_DIRS:
            for p in active_files(folder):
                if intake_id in p.name and p not in found:
                    found.append(p)

    return sorted(found)

def move_files(files, action, intake_id):
    moved = []

    if action in NO_MOVE_ACTIONS:
        return moved

    if action == "ARCHIVIEREN":
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        target_root = DIRS["archiv"] / f"{ts}_vorzimmer_entscheidung_{intake_id or 'ohne_intake'}"
    else:
        target_root = ACTION_TARGETS[action]

    target_root.mkdir(parents=True, exist_ok=True)

    for src in files:
        dst = safe_unique(target_root / src.name)
        shutil.move(str(src), str(dst))
        moved.append({"from": str(src), "to": str(dst)})

    return moved

def read_decisions(csv_path):
    rows = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            if not row:
                continue

            action = normalize_action(row.get("aktion", ""))
            intake_id = str(row.get("intake_id", "") or "").strip()
            source_path = str(row.get("source_path", "") or "").strip()

            if not action:
                continue

            if str(row.get("decision_id", "")).strip().upper() == "BEISPIEL_NICHT_AUSFUEHREN":
                continue

            rows.append({
                "decision_id": str(row.get("decision_id", "") or "").strip(),
                "intake_id": intake_id,
                "source_path": source_path,
                "aktion": action,
                "begruendung": str(row.get("begruendung", "") or "").strip(),
                "frist": str(row.get("frist", "") or "").strip(),
                "verantwortlich": str(row.get("verantwortlich", "") or "").strip(),
                "csv_file": str(csv_path),
            })

    return rows

def process_decision(row):
    action = row["aktion"]

    if action not in VALID_ACTIONS:
        raise RuntimeError("Unzulässige Aktion: " + action)

    intake_id = row["intake_id"]
    source_path = row["source_path"]

    if not intake_id and not source_path:
        raise RuntimeError("Entscheidung ohne intake_id und ohne source_path.")

    files = matching_files(intake_id, source_path)

    if not files and action not in NO_MOVE_ACTIONS:
        raise RuntimeError("Keine passende Arbeitsdatei gefunden für intake_id/source_path.")

    moved = move_files(files, action, intake_id)

    proof = {
        "time": now(),
        "decision": row,
        "matched_files": [str(x) for x in files],
        "moved_files": moved,
        "status": "OK",
    }

    proof_name = (row["decision_id"] or intake_id or "entscheidung").replace(" ", "_")
    proof_path = PROOF_DIR / f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{proof_name}_nachweis.json"
    proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    return proof

def move_decision_file(csv_path, ok):
    target_dir = PROCESSED_DIR if ok else FAILED_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target = safe_unique(target_dir / csv_path.name)
    shutil.move(str(csv_path), str(target))
    return target

def write_reports(results):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = REPORT_DIR / f"VORZIMMER_ENTSCHEIDUNG_V1_{ts}.txt"
    csv_file = REPORT_DIR / f"VORZIMMER_ENTSCHEIDUNG_V1_{ts}.csv"
    json_file = REPORT_DIR / f"VORZIMMER_ENTSCHEIDUNG_V1_{ts}.json"

    data = {
        "time": now(),
        "results_count": len(results),
        "results": results,
        "input_rule": "Nur CSV-Dateien mit Präfix " + INPUT_PREFIX + " werden als Eingabe verarbeitet.",
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = ["csv_file", "decision_id", "intake_id", "aktion", "status", "message", "moved_count"]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()

        for r in results:
            writer.writerow({
                "csv_file": r.get("csv_file", ""),
                "decision_id": r.get("decision_id", ""),
                "intake_id": r.get("intake_id", ""),
                "aktion": r.get("aktion", ""),
                "status": r.get("status", ""),
                "message": r.get("message", ""),
                "moved_count": r.get("moved_count", 0),
            })

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("VORZIMMER ENTSCHEIDUNG V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Entscheidungen: " + str(len(results)) + "\n")
        f.write("Eingaberegel: " + data["input_rule"] + "\n\n")

        if not results:
            f.write("Keine Eingabe-CSV gefunden. Vorlage wurde bereitgestellt.\n")
        else:
            for i, r in enumerate(results, start=1):
                f.write(str(i) + ". " + r.get("aktion", "") + " | " + r.get("status", "") + "\n")
                f.write("Intake-ID: " + r.get("intake_id", "") + "\n")
                f.write("Meldung: " + r.get("message", "") + "\n")
                f.write("Verschobene Dateien: " + str(r.get("moved_count", 0)) + "\n\n")

    return txt, csv_file, json_file

def main():
    ensure_dirs()
    write_template()

    files = decision_csv_files()
    results = []

    for csv_path in files:
        csv_ok = True

        try:
            rows = read_decisions(csv_path)

            for row in rows:
                try:
                    proof = process_decision(row)
                    results.append({
                        "csv_file": str(csv_path),
                        "decision_id": row.get("decision_id", ""),
                        "intake_id": row.get("intake_id", ""),
                        "aktion": row.get("aktion", ""),
                        "status": "OK",
                        "message": "Entscheidung verarbeitet.",
                        "moved_count": len(proof.get("moved_files", [])),
                    })
                except Exception as exc:
                    csv_ok = False
                    results.append({
                        "csv_file": str(csv_path),
                        "decision_id": row.get("decision_id", ""),
                        "intake_id": row.get("intake_id", ""),
                        "aktion": row.get("aktion", ""),
                        "status": "FEHLER",
                        "message": repr(exc),
                        "moved_count": 0,
                    })

        except Exception as exc:
            csv_ok = False
            results.append({
                "csv_file": str(csv_path),
                "decision_id": "",
                "intake_id": "",
                "aktion": "",
                "status": "FEHLER",
                "message": repr(exc),
                "moved_count": 0,
            })

        move_decision_file(csv_path, csv_ok)

    txt, csv_file, json_file = write_reports(results)
    errors = [r for r in results if r.get("status") == "FEHLER"]

    print("")
    print("VORZIMMER_ENTSCHEIDUNG_V1 FERTIG")
    print("Entscheidungen:", len(results))
    print("Fehler:", len(errors))
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("Vorlage:", CONFIG_TEMPLATE)
    print("Eingabeordner:", INPUT_DIR)
    print("Berichte:", REPORT_DIR)

    if errors:
        sys.exit(1)

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
