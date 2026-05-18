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
LOG_DIR = ROOT / "Windows_App" / "Logs"

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
    "protokolle": POST / "90_Protokolle",
    "karten": POST / "91_Entscheidungskarten",
    "sicherheit": POST / "92_Sicherheitsberichte",
    "sprachen": POST / "93_Sprachberichte",
    "archiv": POST / "99_Archiv_Altlasten",
}

WORK_KEYS = [
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

EVIDENCE_KEYS = [
    "protokolle",
    "karten",
    "sicherheit",
    "sprachen",
    "archiv",
]

IGNORE_NAMES = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)
        keep = path / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def list_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE_NAMES
    ])

def collect_status():
    ensure_dirs()

    work_counts = {}
    evidence_counts = {}
    work_files = {}
    evidence_files = {}

    for key in WORK_KEYS:
        files = list_files(DIRS[key])
        work_counts[key] = len(files)
        work_files[key] = [str(x) for x in files]

    for key in EVIDENCE_KEYS:
        files = list_files(DIRS[key])
        evidence_counts[key] = len(files)
        evidence_files[key] = [str(x) for x in files]

    actions = []

    if work_counts["roh"] > 0:
        actions.append("ROHDATEIEN_VERARBEITEN")

    if work_counts["quarantaene"] > 0:
        actions.append("QUARANTAENE_PRUEFEN")

    if work_counts["signatur"] > 0:
        actions.append("SIGNATURPRUEFUNG_ERFORDERLICH")

    if work_counts["rueckfrage"] > 0:
        actions.append("RUECKFRAGE_ABSENDER_OFFEN")

    if work_counts["vorzimmer"] > 0:
        actions.append("VORZIMMER_ENTSCHEIDUNG_OFFEN")

    if work_counts["anwalt"] > 0:
        actions.append("ANWALTVORLAGE_OFFEN")

    if work_counts["sprachpruefung"] > 0:
        actions.append("SPRACHPRUEFUNG_OFFEN")

    if not actions:
        actions.append("KEINE_ARBEITSDATEIEN_OFFEN")

    total_work = sum(work_counts.values())
    total_evidence = sum(evidence_counts.values())

    if total_work == 0:
        operational_status = "ARBEITSPOSTEINGANG_LEER"
    else:
        operational_status = "ARBEITSPOSTEINGANG_OFFEN"

    return {
        "time": now(),
        "root": str(ROOT),
        "posteingang": str(POST),
        "operational_status": operational_status,
        "actions": actions,
        "work_counts": work_counts,
        "evidence_counts": evidence_counts,
        "total_work_files": total_work,
        "total_evidence_files": total_evidence,
        "work_files": work_files,
        "evidence_files": evidence_files,
        "definition": {
            "work_dirs": WORK_KEYS,
            "evidence_dirs": EVIDENCE_KEYS,
            "note": "Protokolle, Sicherheitsberichte, Sprachberichte und Archivdateien sind Nachweise, keine offenen Arbeitsdateien."
        }
    }

def write_reports(data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = LOG_DIR / f"POSTEINGANG_BETRIEBSSTATUS_V1_{ts}.txt"
    jsn = LOG_DIR / f"POSTEINGANG_BETRIEBSSTATUS_V1_{ts}.json"
    csv_file = LOG_DIR / f"POSTEINGANG_BETRIEBSSTATUS_V1_{ts}.csv"

    jsn.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["bereich", "art", "anzahl"])
        for key, value in data["work_counts"].items():
            writer.writerow([key, "arbeit", value])
        for key, value in data["evidence_counts"].items():
            writer.writerow([key, "nachweis", value])

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG BETRIEBSSTATUS V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Status: " + data["operational_status"] + "\n")
        f.write("Offene Arbeitsdateien: " + str(data["total_work_files"]) + "\n")
        f.write("Nachweisdateien: " + str(data["total_evidence_files"]) + "\n")
        f.write("Aktionen: " + ", ".join(data["actions"]) + "\n\n")

        f.write("ARBEITSBEREICHE\n")
        f.write("-" * 80 + "\n")
        for key, value in data["work_counts"].items():
            f.write(f"{key}: {value}\n")

        f.write("\nNACHWEISBEREICHE\n")
        f.write("-" * 80 + "\n")
        for key, value in data["evidence_counts"].items():
            f.write(f"{key}: {value}\n")

        f.write("\nOFFENE ARBEITSDATEIEN\n")
        f.write("-" * 80 + "\n")
        for key, files in data["work_files"].items():
            if files:
                f.write("\n[" + key + "]\n")
                for file in files:
                    f.write(file + "\n")

    return txt, csv_file, jsn

def main():
    data = collect_status()
    txt, csv_file, jsn = write_reports(data)

    print("")
    print("POSTEINGANG_BETRIEBSSTATUS_V1 FERTIG")
    print("Status:", data["operational_status"])
    print("Offene Arbeitsdateien:", data["total_work_files"])
    print("Nachweisdateien:", data["total_evidence_files"])
    print("Aktionen:", ", ".join(data["actions"]))
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", jsn)

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
