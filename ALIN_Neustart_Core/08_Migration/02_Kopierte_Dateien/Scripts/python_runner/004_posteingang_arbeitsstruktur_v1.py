import sys
import csv
import json
import shutil
import hashlib
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(r"I:\KI_Legal_Project")
POST_DIR = ROOT / "Posteingang"

DIRS = {
    "roh": POST_DIR / "00_Roh_Eingang",
    "quarantaene": POST_DIR / "01_Quarantaene",
    "geprueft": POST_DIR / "02_Technisch_Geprueft",
    "vorzimmer": POST_DIR / "03_Vorzimmer_Entscheidung",
    "anwalt": POST_DIR / "04_Anwaltvorlage",
    "rueckfrage": POST_DIR / "05_Rueckfrage_Absender",
    "abgewiesen": POST_DIR / "06_Abgewiesen",
    "protokolle": POST_DIR / "90_Protokolle",
    "karten": POST_DIR / "91_Entscheidungskarten"
}

ACTIVE_EXT = {
    ".exe", ".dll", ".com", ".scr", ".bat", ".cmd", ".ps1", ".vbs",
    ".js", ".jse", ".wsf", ".msi", ".msp", ".hta", ".jar", ".lnk", ".reg"
}

SAFE_DOC_EXT = {
    ".pdf", ".txt", ".rtf", ".docx", ".xlsx", ".pptx",
    ".odt", ".ods", ".odp", ".jpg", ".jpeg", ".png",
    ".tif", ".tiff", ".eml", ".msg"
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    readme = POST_DIR / "README_POSTEINGANG.md"
    readme.write_text(
        "# Posteingang\n\n"
        "Dieser Bereich ist der vorgelagerte Sicherheits- und Entscheidungsbereich.\n\n"
        "Ungeprüfte Dateien dürfen nicht unmittelbar in den normalen Dokumentenbestand übernommen werden.\n",
        encoding="utf-8",
        newline="\n"
    )

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def head_type(path):
    with open(path, "rb") as f:
        h = f.read(4096)

    ext = path.suffix.lower()

    if h.startswith(b"%PDF-"):
        return "PDF"
    if h.startswith(b"PK\x03\x04"):
        if ext == ".docx":
            return "DOCX"
        if ext == ".xlsx":
            return "XLSX"
        if ext == ".pptx":
            return "PPTX"
        if ext in {".odt", ".ods", ".odp"}:
            return "OPENDOCUMENT"
        return "ZIP_CONTAINER"
    if h.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if h.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    try:
        h.decode("utf-8")
        return "TEXT"
    except Exception:
        return "UNBEKANNT"

def classify(path):
    ext = path.suffix.lower()
    suffixes = [s.lower() for s in path.suffixes]
    size = path.stat().st_size
    dtype = head_type(path)

    status = "TECHNISCH_FREIGEGEBEN_VORZIMMER"
    risk = "niedrig"
    reasons = []

    if size == 0:
        status = "TECHNISCH_GESPERRT"
        risk = "hoch"
        reasons.append("Datei ist leer.")

    if ext in ACTIVE_EXT:
        status = "TECHNISCH_GESPERRT"
        risk = "hoch"
        reasons.append("Aktive oder ausführbare Dateiendung.")

    if len(suffixes) >= 2 and suffixes[-1] in ACTIVE_EXT:
        status = "TECHNISCH_GESPERRT"
        risk = "hoch"
        reasons.append("Doppelte Dateiendung mit ausführbarem Endtyp.")

    if ext not in SAFE_DOC_EXT and ext not in ACTIVE_EXT:
        status = "TECHNISCH_UNKLAR_QUARANTAENE"
        risk = "mittel"
        reasons.append("Dateityp ist nicht in der ersten sicheren Dokumentenliste enthalten.")

    if dtype == "ZIP_CONTAINER":
        status = "TECHNISCH_UNKLAR_QUARANTAENE"
        risk = "mittel"
        reasons.append("ZIP-Container ohne freigegebene Dokumentenendung.")

    if not reasons:
        reasons.append("Keine Sperrregel ausgelöst.")

    return {
        "extension": ext,
        "size_bytes": size,
        "detected_type": dtype,
        "risk_level": risk,
        "status": status,
        "reason": " ".join(reasons)
    }

def safe_name(intake_id, name):
    clean = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name)
    return intake_id + "__" + clean

def recommendation(status):
    if status == "TECHNISCH_FREIGEGEBEN_VORZIMMER":
        return "Vorzimmerentscheidung: Anwaltvorlage, Aktenzuordnung, Rückfrage oder Zurückweisung."
    if status == "TECHNISCH_UNKLAR_QUARANTAENE":
        return "Nicht in den normalen Bestand übernehmen. Rückfrage oder technische Nachprüfung."
    return "Nicht öffnen. Rückfrage, Zurückweisung oder gesonderte technische Prüfung."

def create_test_files():
    raw = DIRS["roh"]
    if any(p.is_file() and p.name != ".gitkeep" for p in raw.iterdir()):
        return

    (raw / "TEST_001_Arbeitsvertrag_ungefaehrlich.txt").write_text(
        "Testdatei Posteingang. Keine echte Mandantendatei.\n",
        encoding="utf-8",
        newline="\n"
    )

    (raw / "TEST_002_aktive_Datei_muss_in_Quarantaene.ps1").write_text(
        "Write-Host 'Diese Testdatei darf nicht normal übernommen werden.'\n",
        encoding="utf-8",
        newline="\n"
    )

def process_file(path):
    digest = sha256_file(path)
    data = classify(path)
    intake_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + digest[:12]

    if data["status"] == "TECHNISCH_FREIGEGEBEN_VORZIMMER":
        target_dir = DIRS["geprueft"]
        card_dir = DIRS["vorzimmer"]
    else:
        target_dir = DIRS["quarantaene"]
        card_dir = DIRS["rueckfrage"]

    target = target_dir / safe_name(intake_id, path.name)
    shutil.move(str(path), str(target))

    rec = {
        "intake_id": intake_id,
        "received_at": now(),
        "original_name": path.name,
        "stored_path": str(target),
        "sha256": digest,
        "size_bytes": data["size_bytes"],
        "extension": data["extension"],
        "detected_type": data["detected_type"],
        "risk_level": data["risk_level"],
        "status": data["status"],
        "reason": data["reason"],
        "decision_recommendation": recommendation(data["status"])
    }

    card = card_dir / f"{intake_id}_entscheidungskarte.json"
    card.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    rec["decision_card"] = str(card)
    return rec

def main():
    ensure_dirs()

    if "--create-test" in sys.argv:
        create_test_files()

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = DIRS["protokolle"]

    protocol = log_dir / f"POSTEINGANG_ARBEITSSTRUKTUR_V1_{ts}.txt"
    csv_file = log_dir / f"POSTEINGANG_ARBEITSSTRUKTUR_V1_{ts}.csv"
    jsonl_file = log_dir / f"POSTEINGANG_ARBEITSSTRUKTUR_V1_{ts}.jsonl"

    records = []

    for file in sorted(DIRS["roh"].iterdir()):
        if file.is_file() and file.name != ".gitkeep":
            try:
                records.append(process_file(file))
            except Exception as e:
                records.append({
                    "intake_id": "FEHLER",
                    "received_at": now(),
                    "original_name": file.name,
                    "stored_path": str(file),
                    "sha256": "",
                    "size_bytes": file.stat().st_size if file.exists() else 0,
                    "extension": file.suffix.lower(),
                    "detected_type": "FEHLER",
                    "risk_level": "hoch",
                    "status": "FEHLER_BEI_TECHNISCHER_PRUEFUNG",
                    "reason": repr(e),
                    "decision_recommendation": "Nicht öffnen. Technische Prüfung fehlgeschlagen.",
                    "decision_card": ""
                })

    fields = [
        "intake_id", "received_at", "original_name", "stored_path", "sha256",
        "size_bytes", "extension", "detected_type", "risk_level", "status",
        "reason", "decision_recommendation", "decision_card"
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
        f.write("POSTEINGANG ARBEITSSTRUKTUR V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Verarbeitete Dateien: " + str(len(records)) + "\n\n")
        for k, v in DIRS.items():
            f.write(k + ": " + str(v) + "\n")
        f.write("\nERGEBNISSE\n")
        f.write("-" * 80 + "\n")
        for r in records:
            f.write(f"{r.get('intake_id')} | {r.get('original_name')} | {r.get('status')} | {r.get('risk_level')}\n")

    print("")
    print("POSTEINGANG_ARBEITSSTRUKTUR_V1 FERTIG")
    print("Protokoll:", protocol)
    print("CSV:", csv_file)
    print("JSONL:", jsonl_file)
    print("Verarbeitete Dateien:", len(records))

if __name__ == "__main__":
    main()
