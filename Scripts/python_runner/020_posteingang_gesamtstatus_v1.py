# -*- coding: utf-8 -*-
import sys
import csv
import json
import datetime
import subprocess
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

WORK_DIRS = {
    "00_Roh_Eingang": POST / "00_Roh_Eingang",
    "01_Quarantaene": POST / "01_Quarantaene",
    "02_Technisch_Geprueft": POST / "02_Technisch_Geprueft",
    "03_Vorzimmer_Entscheidung": POST / "03_Vorzimmer_Entscheidung",
    "04_Anwaltvorlage": POST / "04_Anwaltvorlage",
    "05_Rueckfrage_Absender": POST / "05_Rueckfrage_Absender",
    "06_Abgewiesen": POST / "06_Abgewiesen",
    "07_Signaturpruefung": POST / "07_Signaturpruefung",
    "08_Sprachpruefung": POST / "08_Sprachpruefung",
}

EVIDENCE_DIRS = {
    "90_Protokolle": POST / "90_Protokolle",
    "91_Entscheidungskarten": POST / "91_Entscheidungskarten",
    "92_Sicherheitsberichte": POST / "92_Sicherheitsberichte",
    "93_Sprachberichte": POST / "93_Sprachberichte",
    "99_Archiv_Altlasten": POST / "99_Archiv_Altlasten",
}

REQUIRED_FILES = [
    ROOT / "Scripts" / "python_runner" / "005_posteingang_sicherheitsgate_v2.py",
    ROOT / "Scripts" / "python_runner" / "012_posteingang_sprachkontext_gate_v2.py",
    ROOT / "Scripts" / "python_runner" / "014_posteingang_pipeline_v1.py",
    ROOT / "Scripts" / "python_runner" / "015_posteingang_pipeline_smoketest_v1.py",
    ROOT / "Scripts" / "python_runner" / "016_posteingang_betriebsstatus_v1.py",
    ROOT / "Scripts" / "python_runner" / "017_vorzimmer_arbeitsliste_v1.py",
    ROOT / "Scripts" / "python_runner" / "018_vorzimmer_entscheidung_v1.py",
    ROOT / "Scripts" / "python_runner" / "019_vorzimmer_entscheidung_smoketest_v1.py",
    ROOT / "Scripts" / "Run_Posteingang_Pipeline.ps1",
    ROOT / "Scripts" / "Run_Vorzimmer_Arbeitsliste.ps1",
    ROOT / "Scripts" / "Run_Vorzimmer_Entscheidung.ps1",
    ROOT / "Config" / "vorzimmer_entscheidung_template_v1.csv",
]

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    LOG.mkdir(parents=True, exist_ok=True)
    for path in list(WORK_DIRS.values()) + list(EVIDENCE_DIRS.values()):
        path.mkdir(parents=True, exist_ok=True)
        keep = path / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def list_real_files(path):
    if not path.exists():
        return []
    return sorted([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def git_summary():
    try:
        p = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--short"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return {
            "available": True,
            "exit_code": p.returncode,
            "status_short": p.stdout.strip(),
            "clean": p.returncode == 0 and not p.stdout.strip()
        }
    except Exception as exc:
        return {
            "available": False,
            "exit_code": None,
            "status_short": repr(exc),
            "clean": False
        }

def database_summary():
    result = {
        "database": str(DB),
        "exists": DB.exists(),
        "duckdb_available": False,
        "ok": False,
        "error": "",
        "lang_tables": [],
        "posteingang_tables": [],
        "eu24_count": None,
        "case_templates_count": None,
        "participant_profiles_count": None,
    }

    if not DB.exists():
        result["error"] = "Datenbank fehlt."
        return result

    try:
        import duckdb
        result["duckdb_available"] = True

        con = duckdb.connect(str(DB), read_only=True)

        rows = con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()

        names = [x[0] for x in rows]

        result["lang_tables"] = [x for x in names if x.startswith("lang_")]
        result["posteingang_tables"] = [x for x in names if x.startswith("posteingang_")]

        if "lang_language_catalog" in names:
            result["eu24_count"] = con.execute(
                "SELECT COUNT(*) FROM lang_language_catalog WHERE eu_official = TRUE"
            ).fetchone()[0]

        if "lang_case_language_settings" in names:
            result["case_templates_count"] = con.execute(
                "SELECT COUNT(*) FROM lang_case_language_settings"
            ).fetchone()[0]

        if "lang_participant_language_settings" in names:
            result["participant_profiles_count"] = con.execute(
                "SELECT COUNT(*) FROM lang_participant_language_settings"
            ).fetchone()[0]

        con.close()

        result["ok"] = True
        return result

    except Exception as exc:
        result["error"] = repr(exc)
        return result

def collect_status():
    ensure_dirs()

    work = {}
    evidence = {}
    work_files = {}
    missing_required_files = []
    missing_required_dirs = []

    for name, path in WORK_DIRS.items():
        if not path.exists():
            missing_required_dirs.append(str(path))
        files = list_real_files(path)
        work[name] = len(files)
        work_files[name] = [str(x) for x in files]

    for name, path in EVIDENCE_DIRS.items():
        if not path.exists():
            missing_required_dirs.append(str(path))
        evidence[name] = len(list_real_files(path))

    for path in REQUIRED_FILES:
        if not path.exists():
            missing_required_files.append(str(path))

    total_work = sum(work.values())
    total_evidence = sum(evidence.values())

    actions = []

    if work["00_Roh_Eingang"] > 0:
        actions.append("PRODUKTIONSLAUF_STARTEN")

    if work["01_Quarantaene"] > 0:
        actions.append("QUARANTAENE_PRUEFEN")

    if work["07_Signaturpruefung"] > 0:
        actions.append("SIGNATURPRUEFUNG_ENTSCHEIDEN")

    if work["08_Sprachpruefung"] > 0:
        actions.append("SPRACHPRUEFUNG_ENTSCHEIDEN")

    if work["03_Vorzimmer_Entscheidung"] > 0 or work["05_Rueckfrage_Absender"] > 0 or work["04_Anwaltvorlage"] > 0:
        actions.append("VORZIMMER_ARBEITSLISTE_ERZEUGEN")

    if not actions:
        actions.append("KEINE_OFFENE_ARBEIT")

    if missing_required_files or missing_required_dirs:
        system_status = "UNVOLLSTAENDIG"
    elif total_work == 0:
        system_status = "BEREIT_LEER"
    else:
        system_status = "BEREIT_MIT_OFFENER_ARBEIT"

    return {
        "time": now(),
        "root": str(ROOT),
        "posteingang": str(POST),
        "system_status": system_status,
        "total_work_files": total_work,
        "total_evidence_files": total_evidence,
        "work_counts": work,
        "evidence_counts": evidence,
        "work_files": work_files,
        "actions": actions,
        "missing_required_files": missing_required_files,
        "missing_required_dirs": missing_required_dirs,
        "database": database_summary(),
        "git": git_summary(),
    }

def write_reports(data):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = LOG / f"POSTEINGANG_GESAMTSTATUS_V1_{ts}.txt"
    csv_file = LOG / f"POSTEINGANG_GESAMTSTATUS_V1_{ts}.csv"
    json_file = LOG / f"POSTEINGANG_GESAMTSTATUS_V1_{ts}.json"

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["bereich", "art", "anzahl"])

        for key, value in data["work_counts"].items():
            writer.writerow([key, "arbeit", value])

        for key, value in data["evidence_counts"].items():
            writer.writerow([key, "nachweis", value])

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG GESAMTSTATUS V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Status: " + data["system_status"] + "\n")
        f.write("Offene Arbeitsdateien: " + str(data["total_work_files"]) + "\n")
        f.write("Nachweisdateien: " + str(data["total_evidence_files"]) + "\n")
        f.write("Aktionen: " + ", ".join(data["actions"]) + "\n")
        f.write("Git sauber: " + str(data["git"].get("clean")) + "\n")
        f.write("Datenbank prüfbar: " + str(data["database"].get("ok")) + "\n\n")

        f.write("ARBEITSBEREICHE\n")
        f.write("-" * 80 + "\n")
        for key, value in data["work_counts"].items():
            f.write(f"{key}: {value}\n")

        f.write("\nNACHWEISBEREICHE\n")
        f.write("-" * 80 + "\n")
        for key, value in data["evidence_counts"].items():
            f.write(f"{key}: {value}\n")

        f.write("\nDATENBANK\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(data["database"], ensure_ascii=False, indent=2) + "\n")

        f.write("\nFEHLENDE PFLICHTDATEIEN\n")
        f.write("-" * 80 + "\n")
        if not data["missing_required_files"]:
            f.write("Keine.\n")
        else:
            for item in data["missing_required_files"]:
                f.write(item + "\n")

        f.write("\nOFFENE ARBEITSDATEIEN\n")
        f.write("-" * 80 + "\n")
        has_work = False
        for key, files in data["work_files"].items():
            if files:
                has_work = True
                f.write("\n[" + key + "]\n")
                for file in files:
                    f.write(file + "\n")

        if not has_work:
            f.write("Keine.\n")

    return txt, csv_file, json_file

def main():
    data = collect_status()
    txt, csv_file, json_file = write_reports(data)

    print("")
    print("POSTEINGANG_GESAMTSTATUS_V1 FERTIG")
    print("Status:", data["system_status"])
    print("Offene Arbeitsdateien:", data["total_work_files"])
    print("Nachweisdateien:", data["total_evidence_files"])
    print("Aktionen:", ", ".join(data["actions"]))
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", json_file)

    if data["missing_required_files"] or data["missing_required_dirs"]:
        sys.exit(2)

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
