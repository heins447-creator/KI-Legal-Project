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
LOG = ROOT / "Windows_App" / "Logs"
OUT = LOG / "DB_Testlauf_Auswertung"

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

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def newest(base, pattern):
    files = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def read_csv(path):
    if not path or not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

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
    ]:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    if "__" in stem:
        return stem.split("__", 1)[0]
    parts = stem.split("_")
    if len(parts) >= 2 and parts[0].isdigit():
        return parts[0] + "_" + parts[1]
    return stem

def summarize_current_work():
    rows = []
    for key in WORK_KEYS:
        for file in active_files(DIRS[key]):
            rows.append({
                "bereich": key,
                "intake_id": extract_intake_id(file),
                "filename": file.name,
                "path": str(file),
                "size_bytes": file.stat().st_size,
            })
    return rows

def summarize_security_reports():
    rows = []
    for file in active_files(DIRS["sicherheit"]):
        data = read_json(file) or {}
        rows.append({
            "intake_id": extract_intake_id(file),
            "original_name": data.get("original_name", ""),
            "security_status": data.get("security_status", ""),
            "risk_level": data.get("risk_level", ""),
            "signature_evidence": data.get("signature_evidence", ""),
            "defender_scan_started": data.get("defender_scan_started", ""),
            "authenticode_status": data.get("authenticode_status", ""),
            "report": str(file),
        })
    return rows

def summarize_language_reports():
    rows = []
    for file in active_files(DIRS["sprachen"]):
        data = read_json(file) or {}
        rows.append({
            "intake_id": extract_intake_id(file),
            "original_name": data.get("original_name", ""),
            "expected_document_language_code": data.get("expected_document_language_code", ""),
            "detected_actual_language_code": data.get("detected_actual_language_code", ""),
            "language_status": data.get("language_status", ""),
            "translation_required": data.get("translation_required", ""),
            "report": str(file),
        })
    return rows

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    selection_manifest = newest(LOG / "DB_Dateien_Auswahl_Posteingang", "DB_DATEIEN_AUSWAHL_POSTEINGANG_*.csv")
    pipeline_json = newest(POST / "90_Protokolle", "POSTEINGANG_PIPELINE_V1_*.json")
    security_csv = newest(POST / "90_Protokolle", "POSTEINGANG_SICHERHEITSGATE_V2_*.csv")
    language_csv = newest(POST / "90_Protokolle", "POSTEINGANG_SPRACHKONTEXT_GATE_V2_*.csv")
    arbeitsliste_csv = newest(LOG / "Vorzimmer_Arbeitslisten", "VORZIMMER_ARBEITSLISTE_V1_*.csv")
    gesamtstatus_json = newest(LOG, "POSTEINGANG_GESAMTSTATUS_V1_*.json")

    selected_rows = read_csv(selection_manifest)
    security_rows = read_csv(security_csv)
    language_rows = read_csv(language_csv)
    arbeitsliste_rows = read_csv(arbeitsliste_csv)

    work_rows = summarize_current_work()
    security_report_rows = summarize_security_reports()
    language_report_rows = summarize_language_reports()

    summary = {
        "time": now(),
        "selection_manifest": str(selection_manifest) if selection_manifest else "",
        "pipeline_json": str(pipeline_json) if pipeline_json else "",
        "security_csv": str(security_csv) if security_csv else "",
        "language_csv": str(language_csv) if language_csv else "",
        "arbeitsliste_csv": str(arbeitsliste_csv) if arbeitsliste_csv else "",
        "gesamtstatus_json": str(gesamtstatus_json) if gesamtstatus_json else "",
        "selected_count": len(selected_rows),
        "security_rows_count": len(security_rows),
        "language_rows_count": len(language_rows),
        "open_work_count": len(work_rows),
        "arbeitsliste_count": len(arbeitsliste_rows),
        "security_reports_count": len(security_report_rows),
        "language_reports_count": len(language_report_rows),
        "selected_rows": selected_rows,
        "security_rows": security_rows,
        "language_rows": language_rows,
        "open_work": work_rows,
        "arbeitsliste": arbeitsliste_rows,
        "security_reports": security_report_rows,
        "language_reports": language_report_rows,
    }

    out_json = OUT / f"POSTEINGANG_DB_TESTLAUF_AUSWERTUNG_V1_{ts}.json"
    out_txt = OUT / f"POSTEINGANG_DB_TESTLAUF_AUSWERTUNG_V1_{ts}.txt"
    out_csv = OUT / f"POSTEINGANG_DB_TESTLAUF_AUSWERTUNG_V1_{ts}.csv"

    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        fields = ["typ", "intake_id", "name", "status", "sprache", "pfad"]
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()

        for r in selected_rows:
            writer.writerow({
                "typ": "aus_datenbank_gewaehlt",
                "intake_id": "",
                "name": r.get("filename", ""),
                "status": r.get("status", ""),
                "sprache": r.get("language_hint", ""),
                "pfad": r.get("target_path", ""),
            })

        for r in security_report_rows:
            writer.writerow({
                "typ": "sicherheitsbericht",
                "intake_id": r.get("intake_id", ""),
                "name": r.get("original_name", ""),
                "status": r.get("security_status", ""),
                "sprache": "",
                "pfad": r.get("report", ""),
            })

        for r in language_report_rows:
            writer.writerow({
                "typ": "sprachbericht",
                "intake_id": r.get("intake_id", ""),
                "name": r.get("original_name", ""),
                "status": r.get("language_status", ""),
                "sprache": r.get("detected_actual_language_code", ""),
                "pfad": r.get("report", ""),
            })

        for r in work_rows:
            writer.writerow({
                "typ": "offene_arbeitsdatei",
                "intake_id": r.get("intake_id", ""),
                "name": r.get("filename", ""),
                "status": r.get("bereich", ""),
                "sprache": "",
                "pfad": r.get("path", ""),
            })

    with open(out_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG DB-TESTLAUF AUSWERTUNG V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + summary["time"] + "\n\n")

        f.write("QUELLEN\n")
        f.write("-" * 80 + "\n")
        for key in [
            "selection_manifest",
            "pipeline_json",
            "security_csv",
            "language_csv",
            "arbeitsliste_csv",
            "gesamtstatus_json",
        ]:
            f.write(key + ": " + str(summary[key]) + "\n")

        f.write("\nZAHLEN\n")
        f.write("-" * 80 + "\n")
        f.write("Aus Datenbank ausgewählt: " + str(summary["selected_count"]) + "\n")
        f.write("Sicherheitszeilen: " + str(summary["security_rows_count"]) + "\n")
        f.write("Sprachzeilen: " + str(summary["language_rows_count"]) + "\n")
        f.write("Offene Arbeitsdateien: " + str(summary["open_work_count"]) + "\n")
        f.write("Vorzimmer-Arbeitsliste: " + str(summary["arbeitsliste_count"]) + "\n")
        f.write("Sicherheitsberichte: " + str(summary["security_reports_count"]) + "\n")
        f.write("Sprachberichte: " + str(summary["language_reports_count"]) + "\n")

        f.write("\nAUS DATENBANK GEWÄHLTE DATEIEN\n")
        f.write("-" * 80 + "\n")
        for r in selected_rows:
            f.write((r.get("filename") or "") + "\n")
            f.write("Quelle: " + (r.get("source_path") or "") + "\n")
            f.write("Ziel:   " + (r.get("target_path") or "") + "\n")
            f.write("Sprachehinweis: " + (r.get("language_hint") or "") + "\n\n")

        f.write("\nOFFENE ARBEITSDATEIEN\n")
        f.write("-" * 80 + "\n")
        if not work_rows:
            f.write("Keine offenen Arbeitsdateien.\n")
        else:
            for r in work_rows:
                f.write(r["bereich"] + " | " + r["intake_id"] + " | " + r["filename"] + "\n")
                f.write(r["path"] + "\n\n")

        f.write("\nVORZIMMER-ARBEITSLISTE\n")
        f.write("-" * 80 + "\n")
        if not arbeitsliste_rows:
            f.write("Keine offenen Vorzimmerentscheidungen.\n")
        else:
            for r in arbeitsliste_rows:
                f.write((r.get("bereich") or "") + " | " + (r.get("lage") or "") + "\n")
                f.write("Intake-ID: " + (r.get("intake_id") or "") + "\n")
                f.write("Name: " + (r.get("original_name") or "") + "\n")
                f.write("Quelle: " + (r.get("source_path") or "") + "\n\n")

    print("")
    print("POSTEINGANG_DB_TESTLAUF_AUSWERTUNG_V1 FERTIG")
    print("Aus Datenbank ausgewählt:", summary["selected_count"])
    print("Offene Arbeitsdateien:", summary["open_work_count"])
    print("Vorzimmer-Arbeitsliste:", summary["arbeitsliste_count"])
    print("Sicherheitsberichte:", summary["security_reports_count"])
    print("Sprachberichte:", summary["language_reports_count"])
    print("TXT:", out_txt)
    print("CSV:", out_csv)
    print("JSON:", out_json)

    if work_rows:
        print("")
        print("OFFENE ARBEITSDATEIEN:")
        for r in work_rows:
            print(r["bereich"], "|", r["filename"])

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
