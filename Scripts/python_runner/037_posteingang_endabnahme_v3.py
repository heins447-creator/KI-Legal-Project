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

import duckdb

ROOT = Path(r"I:\KI_Legal_Project")
DB = ROOT / "Database" / "Legal_Brain.duckdb"
LOG = ROOT / "Windows_App" / "Logs"
OUT = LOG / "Endabnahmen"
POST = ROOT / "Posteingang"

OUT.mkdir(parents=True, exist_ok=True)

REQUIRED_FILES = [
    ROOT / "START_POSTEINGANG.cmd",
    ROOT / "Scripts" / "Run_Posteingang_Menu.ps1",
    ROOT / "Scripts" / "Run_Posteingang_Zentrale.ps1",
    ROOT / "Scripts" / "Run_Posteingang_Pipeline.ps1",
    ROOT / "Scripts" / "Run_Posteingang_Schlusskontrolle.ps1",
    ROOT / "Scripts" / "Run_Vorzimmer_Arbeitsliste.ps1",
    ROOT / "Scripts" / "Run_Vorzimmer_Entscheidung.ps1",
    ROOT / "Scripts" / "Run_Vorzimmer_Kommunikationsparameter.ps1",
    ROOT / "Scripts" / "python_runner" / "020_posteingang_gesamtstatus_v1.py",
    ROOT / "Scripts" / "python_runner" / "031_dokumentsprachprofil_v1.py",
    ROOT / "Scripts" / "python_runner" / "033_posteingang_schlusskontrolle_v2.py",
    ROOT / "Scripts" / "python_runner" / "035_vorzimmer_kommunikationsparameter_v1.py",
]

REQUIRED_DIRS = [
    POST / "00_Roh_Eingang",
    POST / "01_Quarantaene",
    POST / "02_Technisch_Geprueft",
    POST / "03_Vorzimmer_Entscheidung",
    POST / "04_Anwaltvorlage",
    POST / "05_Rueckfrage_Absender",
    POST / "06_Abgewiesen",
    POST / "07_Signaturpruefung",
    POST / "08_Sprachpruefung",
    POST / "90_Protokolle",
    POST / "91_Entscheidungskarten",
    POST / "92_Sicherheitsberichte",
    POST / "93_Sprachberichte",
    POST / "95_Dokumentsprachprofile",
    POST / "96_Uebersetzung_DE",
    POST / "97_Schlusskontrolle",
    POST / "99_Archiv_Altlasten",
]

WORK_DIRS = [
    POST / "00_Roh_Eingang",
    POST / "01_Quarantaene",
    POST / "02_Technisch_Geprueft",
    POST / "03_Vorzimmer_Entscheidung",
    POST / "04_Anwaltvorlage",
    POST / "05_Rueckfrage_Absender",
    POST / "06_Abgewiesen",
    POST / "07_Signaturpruefung",
    POST / "08_Sprachpruefung",
]

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def count_files(path):
    if not path.exists():
        return 0
    return len([
        p for p in path.rglob("*")
        if p.is_file()
        and p.name not in IGNORE
    ])

def latest_files(pattern, limit=5):
    files = sorted(LOG.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(x) for x in files[:limit]]

def db_checks():
    con = duckdb.connect(str(DB), read_only=True)
    try:
        tables = [x[0] for x in con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()]

        required_tables = [
            "lang_language_catalog",
            "lang_case_language_settings",
            "lang_participant_language_settings",
            "posteingang_document_language_profile",
            "posteingang_document_language_audit",
            "vz_language_package_catalog",
            "vz_communication_context_template",
            "vz_participant_communication_profile",
            "vz_address_language_inference_rule",
        ]

        missing = [t for t in required_tables if t not in tables]

        result = {
            "tables_total": len(tables),
            "missing_required_tables": missing,
            "required_tables_present": len(missing) == 0,
        }

        if "vz_language_package_catalog" in tables:
            result["vz_eu24"] = con.execute(
                "SELECT COUNT(*) FROM vz_language_package_catalog WHERE eu_official = TRUE"
            ).fetchone()[0]

        if "lang_language_catalog" in tables:
            result["lang_eu24"] = con.execute(
                "SELECT COUNT(*) FROM lang_language_catalog WHERE eu_official = TRUE"
            ).fetchone()[0]

        if "vz_communication_context_template" in tables:
            result["se_template_vorzimmer"] = con.execute("""
                SELECT jurisdiction_country_code, official_language_code, procedural_language_code,
                       internal_work_language_code, rough_translation_target_language_code,
                       default_document_language_code
                FROM vz_communication_context_template
                WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
            """).fetchone()

        if "lang_case_language_settings" in tables:
            result["se_template_lang"] = con.execute("""
                SELECT jurisdiction_country_code, country_language_code, procedural_language_code,
                       internal_work_language_code, default_document_language_code
                FROM lang_case_language_settings
                WHERE case_template_key = 'TEMPLATE_SE_ARBEITSRECHT'
            """).fetchone()

        if "posteingang_document_language_profile" in tables:
            result["document_language_profiles"] = con.execute(
                "SELECT COUNT(*) FROM posteingang_document_language_profile"
            ).fetchone()[0]
            result["rough_translation_required"] = con.execute(
                "SELECT COUNT(*) FROM posteingang_document_language_profile WHERE rough_translation_required = TRUE"
            ).fetchone()[0]

        if "vz_participant_communication_profile" in tables:
            result["external_communication_not_sv"] = con.execute("""
                SELECT COUNT(*)
                FROM vz_participant_communication_profile
                WHERE template_key = 'TEMPLATE_SE_ARBEITSRECHT'
                  AND participant_role IN ('gericht', 'gegenseite', 'gegnerischer_anwalt')
                  AND communication_language_code <> 'sv'
            """).fetchone()[0]
            result["mandate_placeholder"] = con.execute("""
                SELECT created_after_mandate_acceptance, accepted_client_required
                FROM vz_participant_communication_profile
                WHERE profile_key = 'SE_ARBEITSRECHT_MANDANT_NACH_ANNAHME'
            """).fetchone()

        return result
    finally:
        con.close()

def validate(data):
    errors = []

    for f in data["required_files"]:
        if not f["exists"]:
            errors.append("Pflichtdatei fehlt: " + f["path"])

    for d in data["required_dirs"]:
        if not d["exists"]:
            errors.append("Pflichtordner fehlt: " + d["path"])

    db = data["database"]

    if not db.get("required_tables_present"):
        errors.append("Pflichttabellen fehlen: " + repr(db.get("missing_required_tables")))

    if db.get("vz_eu24") != 24:
        errors.append("Vorzimmer-EU24-Sprachpakete fehlerhaft: " + repr(db.get("vz_eu24")))

    if db.get("lang_eu24") != 24:
        errors.append("Lang-EU24-Sprachkatalog fehlerhaft: " + repr(db.get("lang_eu24")))

    expected_vz = ("SE", "sv", "sv", "de", "de", "sv")
    if tuple(db.get("se_template_vorzimmer") or ()) != expected_vz:
        errors.append("Vorzimmer-Schwedenvorlage fehlerhaft: " + repr(db.get("se_template_vorzimmer")))

    if db.get("external_communication_not_sv") not in (0, None):
        errors.append("Externe Kommunikation im Schweden-Arbeitsrecht ist nicht vollständig Schwedisch.")

    if tuple(db.get("mandate_placeholder") or ()) != (True, True):
        errors.append("Mandantenplatzhalter nach Mandatsannahme fehlt oder ist fehlerhaft.")

    data["errors"] = errors
    data["status"] = "OK" if not errors else "FEHLER"
    return data

def main():
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    required_files = [{"path": str(p), "exists": p.exists()} for p in REQUIRED_FILES]
    required_dirs = [{"path": str(p), "exists": p.exists()} for p in REQUIRED_DIRS]

    work_counts = {p.name: count_files(p) for p in WORK_DIRS}

    data = {
        "time": now(),
        "root": str(ROOT),
        "database_path": str(DB),
        "required_files": required_files,
        "required_dirs": required_dirs,
        "work_counts": work_counts,
        "open_work_files_total": sum(work_counts.values()),
        "database": db_checks(),
        "latest_reports": {
            "gesamtstatus": latest_files("POSTEINGANG_GESAMTSTATUS_V1_*.txt"),
            "schlusskontrolle": latest_files("POSTEINGANG_SCHLUSSKONTROLLE_V2_*.txt"),
            "dokumentsprachprofil": latest_files("DOKUMENTSPRACHPROFIL_V1_*.txt"),
            "vorzimmer_kommunikation": latest_files("RUN_VORZIMMER_KOMMUNIKATIONSPARAMETER_*.txt"),
            "endabnahme": latest_files("POSTEINGANG_ENDABNAHME_V3_*.txt"),
        },
        "minimum_line": {
            "sicher": "durch Sicherheitsgate und Schlußkontrolle vorgesehen",
            "bearbeitet": "durch Pipeline, Vorzimmer und Schlußkontrolle nachweisbar",
            "sprache_erkannt": "durch Sprachkontext und Dokumentsprachprofil vorgesehen",
            "uebersetzung_deutsch": "grobe Arbeitsübersetzung nach Deutsch vorgesehen",
            "anwaltvorlage": "durch Vorzimmerentscheidung oder Anwaltvorlage steuerbar",
        },
        "boundary": "Posteingang und Vorzimmer bewerten nicht Beweiswert, Entlastungswert, rechtliche Erheblichkeit oder endgültige Aktenzuordnung."
    }

    data = validate(data)

    out_json = OUT / f"POSTEINGANG_ENDABNAHME_V3_{ts}.json"
    out_csv = OUT / f"POSTEINGANG_ENDABNAHME_V3_{ts}.csv"
    out_txt = OUT / f"POSTEINGANG_ENDABNAHME_V3_{ts}.txt"

    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8", newline="\n")

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["bereich", "wert", "status"])
        writer.writerow(["gesamtstatus", data["status"], "OK" if data["status"] == "OK" else "FEHLER"])
        writer.writerow(["offene_arbeitsdateien", data["open_work_files_total"], "INFO"])
        writer.writerow(["vz_eu24", data["database"].get("vz_eu24", ""), "OK" if data["database"].get("vz_eu24") == 24 else "FEHLER"])
        writer.writerow(["lang_eu24", data["database"].get("lang_eu24", ""), "OK" if data["database"].get("lang_eu24") == 24 else "FEHLER"])
        writer.writerow(["document_language_profiles", data["database"].get("document_language_profiles", ""), "INFO"])
        writer.writerow(["errors", len(data["errors"]), "OK" if not data["errors"] else "FEHLER"])

    with open(out_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG ENDABNAHME V3\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Status: " + data["status"] + "\n")
        f.write("Offene Arbeitsdateien: " + str(data["open_work_files_total"]) + "\n\n")

        f.write("MINDESTLINIE JE EINGANG\n")
        f.write("-" * 80 + "\n")
        for k, v in data["minimum_line"].items():
            f.write(k + ": " + v + "\n")

        f.write("\nSCHWEDEN ARBEITSRECHT\n")
        f.write("-" * 80 + "\n")
        f.write("Vorzimmer-Sprachkontext: " + repr(data["database"].get("se_template_vorzimmer")) + "\n")
        f.write("Lang-Sprachkontext: " + repr(data["database"].get("se_template_lang")) + "\n")
        f.write("Externe Kommunikation nicht Schwedisch: " + repr(data["database"].get("external_communication_not_sv")) + "\n")
        f.write("Mandantenplatzhalter: " + repr(data["database"].get("mandate_placeholder")) + "\n")

        f.write("\nDATENBANK\n")
        f.write("-" * 80 + "\n")
        for k, v in data["database"].items():
            f.write(str(k) + ": " + repr(v) + "\n")

        f.write("\nARBEITSBEREICHE\n")
        f.write("-" * 80 + "\n")
        for k, v in data["work_counts"].items():
            f.write(k + ": " + str(v) + "\n")

        f.write("\nFEHLER\n")
        f.write("-" * 80 + "\n")
        if data["errors"]:
            for e in data["errors"]:
                f.write(e + "\n")
        else:
            f.write("Keine Fehler festgestellt.\n")

        f.write("\nGRENZE\n")
        f.write("-" * 80 + "\n")
        f.write(data["boundary"] + "\n")

    print("")
    print("POSTEINGANG_ENDABNAHME_V3 FERTIG")
    print("Status:", data["status"])
    print("Offene Arbeitsdateien:", data["open_work_files_total"])
    print("Fehler:", len(data["errors"]))
    print("TXT:", out_txt)
    print("CSV:", out_csv)
    print("JSON:", out_json)

    if data["errors"]:
        for e in data["errors"]:
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
