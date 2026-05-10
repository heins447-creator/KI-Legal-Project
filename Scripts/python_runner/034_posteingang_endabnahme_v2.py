# -*- coding: utf-8 -*-
import sys
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
OUT = LOG / "Endabnahmen"
DB = ROOT / "Database" / "Legal_Brain.duckdb"

REQUIRED_FILES = [
    "START_POSTEINGANG.cmd",
    "Scripts/Run_Posteingang_Menu.ps1",
    "Scripts/Run_Posteingang_Zentrale.ps1",
    "Scripts/Run_Posteingang_Pipeline.ps1",
    "Scripts/Run_Posteingang_Schlusskontrolle.ps1",
    "Scripts/Run_Vorzimmer_Arbeitsliste.ps1",
    "Scripts/Run_Vorzimmer_Entscheidung.ps1",
    "Scripts/Run_Aktenmaterial_Freigabeliste.ps1",
    "Scripts/Run_Dokumentsprachprofil.ps1",
    "Scripts/python_runner/005_posteingang_sicherheitsgate_v2.py",
    "Scripts/python_runner/012_posteingang_sprachkontext_gate_v2.py",
    "Scripts/python_runner/014_posteingang_pipeline_v1.py",
    "Scripts/python_runner/016_posteingang_betriebsstatus_v1.py",
    "Scripts/python_runner/017_vorzimmer_arbeitsliste_v1.py",
    "Scripts/python_runner/018_vorzimmer_entscheidung_v1.py",
    "Scripts/python_runner/020_posteingang_gesamtstatus_v1.py",
    "Scripts/python_runner/026_posteingang_aktenmaterial_agentenabgrenzung_v1.py",
    "Scripts/python_runner/027_posteingang_aktenmaterial_freigabeliste_v1.py",
    "Scripts/python_runner/031_dokumentsprachprofil_v1.py",
    "Scripts/python_runner/032_check_dokumentsprachprofil_v1.py",
    "Scripts/python_runner/033_posteingang_schlusskontrolle_v2.py",
    "Config/dokumentsprachprofil_v1.json",
    "Config/posteingang_schlusskontrolle_v2.json",
    "Config/posteingang_aktenmaterial_agentenabgrenzung_v1.json",
    "Config/posteingang_aktenmaterial_freigabeliste_v1.json",
]

REQUIRED_DIRS = [
    "Posteingang/00_Roh_Eingang",
    "Posteingang/01_Quarantaene",
    "Posteingang/02_Technisch_Geprueft",
    "Posteingang/03_Vorzimmer_Entscheidung",
    "Posteingang/04_Anwaltvorlage",
    "Posteingang/05_Rueckfrage_Absender",
    "Posteingang/06_Abgewiesen",
    "Posteingang/07_Signaturpruefung",
    "Posteingang/08_Sprachpruefung",
    "Posteingang/90_Protokolle",
    "Posteingang/91_Entscheidungskarten",
    "Posteingang/92_Sicherheitsberichte",
    "Posteingang/93_Sprachberichte",
    "Posteingang/95_Dokumentsprachprofile",
    "Posteingang/96_Uebersetzung_DE",
    "Posteingang/97_Schlusskontrolle",
    "Posteingang/99_Archiv_Altlasten",
]

WORK_DIRS = [
    "00_Roh_Eingang",
    "01_Quarantaene",
    "02_Technisch_Geprueft",
    "03_Vorzimmer_Entscheidung",
    "04_Anwaltvorlage",
    "05_Rueckfrage_Absender",
    "06_Abgewiesen",
    "07_Signaturpruefung",
    "08_Sprachpruefung",
]

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def file_count(path):
    if not path.exists():
        return 0
    return len([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def newest_files(base, patterns, limit=20):
    found = []
    if not base.exists():
        return found
    for pattern in patterns:
        found.extend(base.rglob(pattern))
    found = sorted(set(found), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(x) for x in found[:limit]]

def check_database():
    result = {
        "database_exists": DB.exists(),
        "duckdb_available": False,
        "tables": {},
        "errors": [],
    }

    if not DB.exists():
        result["errors"].append("Datenbank fehlt: " + str(DB))
        return result

    try:
        import duckdb
        result["duckdb_available"] = True
    except Exception as exc:
        result["errors"].append("duckdb nicht importierbar: " + repr(exc))
        return result

    try:
        con = duckdb.connect(str(DB), read_only=True)

        tables = [x[0] for x in con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()]

        wanted = [
            "lang_language_catalog",
            "lang_staff_language_settings",
            "lang_case_language_settings",
            "lang_participant_language_settings",
            "posteingang_document_language_profile",
            "posteingang_document_language_audit",
        ]

        for name in wanted:
            result["tables"][name] = {
                "exists": name in tables,
                "count": None,
            }
            if name in tables:
                try:
                    result["tables"][name]["count"] = con.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
                except Exception as exc:
                    result["tables"][name]["count_error"] = repr(exc)

        if "lang_language_catalog" in tables:
            result["eu24"] = con.execute("SELECT COUNT(*) FROM lang_language_catalog WHERE eu_official = TRUE").fetchone()[0]

        if "lang_case_language_settings" in tables:
            result["schweden_arbeitsrecht"] = con.execute("""
                SELECT jurisdiction_country_code, country_language_code, procedural_language_code,
                       internal_work_language_code, default_document_language_code
                FROM lang_case_language_settings
                WHERE case_template_key = 'TEMPLATE_SE_ARBEITSRECHT'
            """).fetchone()

        con.close()

    except Exception as exc:
        result["errors"].append("Datenbankprüfung fehlgeschlagen: " + repr(exc))

    return result

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_txt = OUT / f"POSTEINGANG_ENDABNAHME_V2_{ts}.txt"
    out_json = OUT / f"POSTEINGANG_ENDABNAHME_V2_{ts}.json"

    missing_files = []
    present_files = []

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if path.exists():
            present_files.append(str(path))
        else:
            missing_files.append(str(path))

    missing_dirs = []
    present_dirs = []

    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        if path.exists():
            present_dirs.append(str(path))
        else:
            missing_dirs.append(str(path))

    work_counts = {}
    for name in WORK_DIRS:
        work_counts[name] = file_count(POST / name)

    total_work = sum(work_counts.values())

    evidence_counts = {
        "90_Protokolle": file_count(POST / "90_Protokolle"),
        "92_Sicherheitsberichte": file_count(POST / "92_Sicherheitsberichte"),
        "93_Sprachberichte": file_count(POST / "93_Sprachberichte"),
        "95_Dokumentsprachprofile": file_count(POST / "95_Dokumentsprachprofile"),
        "96_Uebersetzung_DE": file_count(POST / "96_Uebersetzung_DE"),
        "97_Schlusskontrolle": file_count(POST / "97_Schlusskontrolle"),
        "99_Archiv_Altlasten": file_count(POST / "99_Archiv_Altlasten"),
    }

    db_result = check_database()

    latest = {
        "schlusskontrolle": newest_files(LOG, ["*SCHLUSSKONTROLLE*.txt", "*Schlusskontrolle*.txt"]),
        "gesamtstatus": newest_files(LOG, ["*GESAMTSTATUS*.txt", "*Gesamtstatus*.txt"]),
        "bedienstart": newest_files(LOG, ["*BEDIENSTART*.txt"]),
        "pipeline": newest_files(LOG, ["*PIPELINE*.txt"]),
        "arbeitslisten": newest_files(LOG / "Vorzimmer_Arbeitslisten", ["VORZIMMER_ARBEITSLISTE_V1_*.txt"]),
        "aktenmaterial": newest_files(LOG / "Aktenmaterial_Freigabelisten", ["AKTENMATERIAL_FREIGABELISTE_V1_*.txt"]),
    }

    errors = []

    if missing_files:
        errors.append("Pflichtdateien fehlen: " + str(len(missing_files)))

    if missing_dirs:
        errors.append("Pflichtordner fehlen: " + str(len(missing_dirs)))

    if db_result.get("errors"):
        errors.extend(db_result["errors"])

    if db_result.get("tables", {}).get("lang_language_catalog", {}).get("exists") and db_result.get("eu24") != 24:
        errors.append("EU24-Sprachkatalog ist nicht vollständig.")

    if db_result.get("schweden_arbeitsrecht"):
        row = tuple(db_result["schweden_arbeitsrecht"])
        expected = ("SE", "sv", "sv", "de", "sv")
        if row != expected:
            errors.append("Schweden-Arbeitsrecht-Sprachkontext weicht ab: " + repr(row))
    else:
        errors.append("Schweden-Arbeitsrecht-Sprachkontext nicht prüfbar oder nicht vorhanden.")

    status = "OK" if not errors else "FEHLER"

    data = {
        "time": now(),
        "status": status,
        "root": str(ROOT),
        "missing_files": missing_files,
        "missing_dirs": missing_dirs,
        "work_counts": work_counts,
        "total_open_work_files": total_work,
        "evidence_counts": evidence_counts,
        "database": db_result,
        "latest_reports": latest,
        "errors": errors,
        "minimum_posteingang_requirements": {
            "sicher": "über Sicherheitsgate und Schlußkontrolle nachzuweisen",
            "bearbeitet": "über Pipeline, Status und Schlußkontrolle nachzuweisen",
            "sprache_erkannt": "über Dokumentsprachprofil und Sprachberichte nachzuweisen",
            "uebersetzung_deutsch": "über 96_Uebersetzung_DE oder Platzhalter für grobe Arbeitsübersetzung nachzuweisen",
            "anwaltvorlage": "über 04_Anwaltvorlage oder Vorzimmerentscheidung vorzubereiten",
        },
    }

    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(out_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG ENDABNAHME V2\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Status: " + status + "\n")
        f.write("Offene Arbeitsdateien: " + str(total_work) + "\n\n")

        f.write("PFLICHTDATEIEN\n")
        f.write("-" * 80 + "\n")
        f.write("Vorhanden: " + str(len(present_files)) + "\n")
        f.write("Fehlend: " + str(len(missing_files)) + "\n")
        for x in missing_files:
            f.write("FEHLT: " + x + "\n")

        f.write("\nPFLICHTORDNER\n")
        f.write("-" * 80 + "\n")
        f.write("Vorhanden: " + str(len(present_dirs)) + "\n")
        f.write("Fehlend: " + str(len(missing_dirs)) + "\n")
        for x in missing_dirs:
            f.write("FEHLT: " + x + "\n")

        f.write("\nARBEITSBEREICHE\n")
        f.write("-" * 80 + "\n")
        for k, v in work_counts.items():
            f.write(k + ": " + str(v) + "\n")

        f.write("\nNACHWEISBEREICHE\n")
        f.write("-" * 80 + "\n")
        for k, v in evidence_counts.items():
            f.write(k + ": " + str(v) + "\n")

        f.write("\nDATENBANK\n")
        f.write("-" * 80 + "\n")
        f.write(json.dumps(db_result, ensure_ascii=False, indent=2, default=str) + "\n")

        f.write("\nLETZTE BERICHTE\n")
        f.write("-" * 80 + "\n")
        for k, vals in latest.items():
            f.write("\n[" + k + "]\n")
            for v in vals[:10]:
                f.write(v + "\n")

        f.write("\nFEHLER\n")
        f.write("-" * 80 + "\n")
        if errors:
            for e in errors:
                f.write(e + "\n")
        else:
            f.write("Keine Fehler festgestellt.\n")

    print("")
    print("POSTEINGANG_ENDABNAHME_V2 FERTIG")
    print("Status:", status)
    print("Offene Arbeitsdateien:", total_work)
    print("TXT:", out_txt)
    print("JSON:", out_json)

    if errors:
        for e in errors:
            print("FEHLER:", e)
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
