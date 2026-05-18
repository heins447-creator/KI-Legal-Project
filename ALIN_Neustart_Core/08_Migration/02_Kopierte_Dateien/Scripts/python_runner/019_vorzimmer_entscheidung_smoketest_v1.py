# -*- coding: utf-8 -*-
import sys
import csv
import json
import shutil
import subprocess
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
STARTER = ROOT / "Scripts" / "Run_Vorzimmer_Entscheidung.ps1"

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

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    for p in list(DIRS.values()) + [
        DECISION_DIR,
        DECISION_DIR / "Berichte",
        DECISION_DIR / "Verarbeitet",
        DECISION_DIR / "Fehler",
        DECISION_DIR / "Nachweise",
    ]:
        p.mkdir(parents=True, exist_ok=True)

def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def run_starter():
    p = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(STARTER)
        ],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    if p.stdout:
        print(p.stdout)

    if p.returncode != 0:
        raise RuntimeError("Vorzimmer-Entscheidung-Starter fehlgeschlagen. Exitcode: " + str(p.returncode))

def files_with_marker(base, marker):
    if not base.exists():
        return []

    found = []

    for p in base.rglob("*"):
        if not p.is_file():
            continue

        if marker in p.name:
            found.append(p)
            continue

        try:
            data = p.read_text(encoding="utf-8", errors="ignore")
            if marker in data:
                found.append(p)
        except Exception:
            pass

    return sorted(set(found))

def assert_any(base, marker, label):
    hits = files_with_marker(base, marker)
    if not hits:
        raise RuntimeError("Nachweis fehlt: " + label + " | " + str(base))
    return hits

def archive_marker_files(marker):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive = DIRS["archiv"] / f"{ts}_vorzimmer_entscheidung_smoketest_{marker}"
    manifest = archive / "MANIFEST_VORZIMMER_ENTSCHEIDUNG_SMOKETEST.csv"
    rows = []

    candidates = []

    for p in files_with_marker(POST, marker):
        if "99_Archiv_Altlasten" not in p.parts:
            candidates.append(("Posteingang", p))

    for p in files_with_marker(DECISION_DIR, marker):
        if "Archiv" not in p.parts:
            candidates.append(("Vorzimmer_Entscheidungen", p))

    for root_label, src in sorted(candidates, key=lambda x: str(x[1])):
        if not src.exists():
            continue

        if root_label == "Posteingang":
            rel = Path(root_label) / src.relative_to(POST)
        else:
            rel = Path("Windows_App") / "Logs" / root_label / src.relative_to(DECISION_DIR)

        dst = archive / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            dst = dst.with_name(dst.stem + "__dup" + dst.suffix)

        size = src.stat().st_size
        shutil.move(str(src), str(dst))

        rows.append({
            "original_path": str(src),
            "archive_path": str(dst),
            "size_bytes": size,
        })

    with open(manifest, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["original_path", "archive_path", "size_bytes"], delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return archive, manifest, rows

def remaining_marker_work_files(marker):
    hits = []

    for key, base in DIRS.items():
        if key == "archiv":
            continue

        for p in files_with_marker(base, marker):
            hits.append(p)

    return hits

def main():
    ensure_dirs()

    if not STARTER.exists():
        raise RuntimeError("Starter fehlt: " + str(STARTER))

    marker = "SMOKEDEC_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    intake_a = marker + "_A1"
    intake_b = marker + "_B1"
    intake_c = marker + "_C1"
    intake_d = marker + "_D1"

    write_text(DIRS["geprueft"] / f"{intake_a}__technisch_geprueft.txt", marker + "\ntechnisch geprüft\n")
    write_text(DIRS["signatur"] / f"{intake_b}__signatur_offen.eml", marker + "\nsignatur offen\n")
    write_text(DIRS["quarantaene"] / f"{intake_c}__quarantaene.txt", marker + "\nquarantäne\n")
    write_text(DIRS["vorzimmer"] / f"{intake_d}_sprachkarte.json", json.dumps({
        "marker": marker,
        "intake_id": intake_d,
        "language_status": "SPRACHE_ABWEICHUNG_UEBERSETZUNG_PRUEFEN"
    }, ensure_ascii=False, indent=2))

    decision_csv = DECISION_DIR / f"EINGABE_VORZIMMER_ENTSCHEIDUNG_{marker}.csv"

    rows = [
        {
            "decision_id": marker + "_DEC_A",
            "intake_id": intake_a,
            "source_path": "",
            "aktion": "ANWALTVORLAGE",
            "begruendung": "Smoketest technisch geprüfte Datei an Anwaltvorlage.",
            "frist": "",
            "verantwortlich": "Vorzimmer",
        },
        {
            "decision_id": marker + "_DEC_B",
            "intake_id": intake_b,
            "source_path": "",
            "aktion": "RUECKFRAGE_ABSENDER",
            "begruendung": "Smoketest Signaturfall zur Rückfrage.",
            "frist": "",
            "verantwortlich": "Vorzimmer",
        },
        {
            "decision_id": marker + "_DEC_C",
            "intake_id": intake_c,
            "source_path": "",
            "aktion": "ABWEISEN",
            "begruendung": "Smoketest Quarantänefall abweisen.",
            "frist": "",
            "verantwortlich": "Vorzimmer",
        },
        {
            "decision_id": marker + "_DEC_D",
            "intake_id": intake_d,
            "source_path": "",
            "aktion": "SPRACHPRUEFUNG",
            "begruendung": "Smoketest Sprachkarte in Sprachprüfung.",
            "frist": "",
            "verantwortlich": "Vorzimmer",
        },
    ]

    with open(decision_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["decision_id", "intake_id", "source_path", "aktion", "begruendung", "frist", "verantwortlich"],
            delimiter=";"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print("")
    print("VORZIMMER_ENTSCHEIDUNG_SMOKETEST_V1 START")
    print("Marker:", marker)
    print("Entscheidungsdatei:", decision_csv)

    run_starter()

    assert_any(DIRS["anwalt"], intake_a, "ANWALTVORLAGE")
    assert_any(DIRS["rueckfrage"], intake_b, "RUECKFRAGE_ABSENDER")
    assert_any(DIRS["abgewiesen"], intake_c, "ABWEISEN")
    assert_any(DIRS["sprachpruefung"], intake_d, "SPRACHPRUEFUNG")
    assert_any(DECISION_DIR / "Verarbeitet", marker, "verarbeitete Entscheidungsdatei")
    assert_any(DECISION_DIR / "Nachweise", marker, "Entscheidungsnachweise")
    assert_any(DECISION_DIR / "Berichte", marker, "Entscheidungsberichte")

    archive, manifest, archived = archive_marker_files(marker)
    remaining = remaining_marker_work_files(marker)

    result = {
        "time": now(),
        "marker": marker,
        "archive": str(archive),
        "manifest": str(manifest),
        "archived_count": len(archived),
        "remaining_work_marker_files": [str(x) for x in remaining],
        "status": "OK" if not remaining else "FEHLER",
    }

    result_file = LOG / f"VORZIMMER_ENTSCHEIDUNG_SMOKETEST_V1_{marker}.json"
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    print("")
    print("VORZIMMER_ENTSCHEIDUNG_SMOKETEST_V1 FERTIG")
    print("Marker:", marker)
    print("Archiv:", archive)
    print("Manifest:", manifest)
    print("Archivierte Dateien:", len(archived))
    print("Restliche Arbeitsdateien mit Marker:", len(remaining))
    print("Ergebnis:", result_file)

    if remaining:
        raise RuntimeError("Smoketest hinterließ Arbeitsdateien mit Marker.")

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
