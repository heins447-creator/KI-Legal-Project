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
OUT = LOG / "Aktenmaterial_Freigabelisten"
CONFIG = ROOT / "Config" / "posteingang_aktenmaterial_freigabeliste_v1.json"

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
}

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

CONFIG_DATA = {
    "version": "V1",
    "case_context": {
        "case_type": "Schwedischer Arbeitsrechtsstreit",
        "parties": "Arbeitnehmer gegen kommunalen Arbeitgeber",
        "official_language": "sv",
        "procedural_language": "sv",
        "internal_work_language": "de",
        "substantive_law_context": "schwedisches Arbeitsrecht und schwedisches Verfahren"
    },
    "principle": "Der Posteingang bewertet fallbezogene Dokumente nicht als Beweis, Entlastung, Aussage oder rechtlich erhebliches Material. Er führt sie nur als unbewertetes Aktenmaterial weiter."
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    for p in DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

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

def boundary_for(area):
    if area == "roh":
        return ("NICHT_FREIGEGEBEN", False, "NOCH_NICHT_GEPRUEFT", "Produktionslauf starten")
    if area == "quarantaene":
        return ("GESPERRT", False, "KEIN_AKTENMATERIAL_FUER_AGENTEN", "technische Nachprüfung oder Rückfrage")
    if area == "signatur":
        return ("SIGNATURPRUEFUNG_OFFEN", False, "SIGNATURPRUEFUNG_OFFEN", "Signaturprüfung")
    if area == "sprachpruefung":
        return ("SPRACHKONTEXT_OFFEN", False, "SPRACHKONTEXT_ODER_UEBERSETZUNG_OFFEN", "Sprachprüfung oder Übersetzung")
    if area == "rueckfrage":
        return ("RUECKFRAGE_OFFEN", False, "ORGANISATORISCH_OFFEN", "Rückfrage an Absender")
    if area == "abgewiesen":
        return ("ABGEWIESEN", False, "NICHT_ZUR_BEARBEITUNG", "Archivierung oder Nachweis")
    if area == "vorzimmer":
        return ("VORZIMMERENTSCHEIDUNG_OFFEN", False, "STEUERDATEI_ODER_ENTSCHEIDUNGSKARTE", "Vorzimmerentscheidung")
    if area == "geprueft":
        return ("TECHNISCH_GEPRUEFT", True, "UNBEWERTETES_AKTENMATERIAL", "Vorzimmerfreigabe, Anwaltvorlage oder Agentenbearbeitung")
    if area == "anwalt":
        return ("ANWALTVORLAGE", True, "UNBEWERTETES_AKTENMATERIAL_FUER_ANWALT_ODER_AGENTEN", "anwaltliche oder nachgelagerte Agentenbearbeitung")

    return ("UNBEKANNT", False, "UNGEKLAERT", "manuelle Prüfung")

def build_entries():
    ensure_dirs()
    entries = []

    for area, folder in DIRS.items():
        for file in active_files(folder):
            freigabe, agent_ok, aktenstatus, step = boundary_for(area)

            entries.append({
                "time": now(),
                "area": area,
                "intake_id": extract_intake_id(file),
                "filename": file.name,
                "path": str(file),
                "freigabestatus": freigabe,
                "agentenbearbeitung": agent_ok,
                "aktenmaterial_status": aktenstatus,
                "naechster_schritt": step,
                "inhaltliche_bewertung_im_posteingang": "NEIN",
                "beweisbewertung": "NICHT_IM_POSTEINGANG",
                "entlastungsbewertung": "NICHT_IM_POSTEINGANG",
                "aussagebewertung": "NICHT_IM_POSTEINGANG",
                "rechtliche_relevanz": "NICHT_IM_POSTEINGANG",
            })

    entries.sort(key=lambda x: (0 if x["agentenbearbeitung"] else 1, x["area"], x["filename"]))
    return entries

def write_reports(entries):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"AKTENMATERIAL_FREIGABELISTE_V1_{ts}.txt"
    csv_file = OUT / f"AKTENMATERIAL_FREIGABELISTE_V1_{ts}.csv"
    json_file = OUT / f"AKTENMATERIAL_FREIGABELISTE_V1_{ts}.json"

    data = {
        "time": now(),
        "entries_count": len(entries),
        "agent_ready_count": sum(1 for x in entries if x["agentenbearbeitung"]),
        "blocked_count": sum(1 for x in entries if not x["agentenbearbeitung"]),
        "case_context": CONFIG_DATA["case_context"],
        "principle": CONFIG_DATA["principle"],
        "entries": entries,
    }

    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "time",
        "area",
        "intake_id",
        "filename",
        "path",
        "freigabestatus",
        "agentenbearbeitung",
        "aktenmaterial_status",
        "naechster_schritt",
        "inhaltliche_bewertung_im_posteingang",
        "beweisbewertung",
        "entlastungsbewertung",
        "aussagebewertung",
        "rechtliche_relevanz",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for e in entries:
            writer.writerow(e)

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("AKTENMATERIAL FREIGABELISTE V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Einträge: " + str(data["entries_count"]) + "\n")
        f.write("Für nachgelagerte Agenten möglich: " + str(data["agent_ready_count"]) + "\n")
        f.write("Gesperrt oder offen: " + str(data["blocked_count"]) + "\n\n")

        f.write("FALLKONTEXT\n")
        f.write("-" * 80 + "\n")
        f.write("Schwedischer Arbeitsrechtsstreit Arbeitnehmer gegen kommunalen Arbeitgeber\n")
        f.write("Amtssprache: Schwedisch\n")
        f.write("Prozeßsprache: Schwedisch\n")
        f.write("Interne Arbeitssprache: Deutsch\n\n")

        f.write("LEITLINIE\n")
        f.write("-" * 80 + "\n")
        f.write(CONFIG_DATA["principle"] + "\n\n")

        if not entries:
            f.write("Keine offenen Arbeitsdateien gefunden.\n")
        else:
            for i, e in enumerate(entries, start=1):
                f.write(str(i) + ". " + e["filename"] + "\n")
                f.write("-" * 80 + "\n")
                f.write("Bereich: " + e["area"] + "\n")
                f.write("Intake-ID: " + e["intake_id"] + "\n")
                f.write("Pfad: " + e["path"] + "\n")
                f.write("Freigabestatus: " + e["freigabestatus"] + "\n")
                f.write("Agentenbearbeitung: " + str(e["agentenbearbeitung"]) + "\n")
                f.write("Aktenmaterialstatus: " + e["aktenmaterial_status"] + "\n")
                f.write("Nächster Schritt: " + e["naechster_schritt"] + "\n")
                f.write("Beweisbewertung: NICHT_IM_POSTEINGANG\n")
                f.write("Entlastungsbewertung: NICHT_IM_POSTEINGANG\n")
                f.write("Aussagebewertung: NICHT_IM_POSTEINGANG\n\n")

    return txt, csv_file, json_file, data

def main():
    entries = build_entries()
    txt, csv_file, json_file, data = write_reports(entries)

    print("")
    print("POSTEINGANG_AKTENMATERIAL_FREIGABELISTE_V1 FERTIG")
    print("Eintraege:", data["entries_count"])
    print("Agentenbearbeitung moeglich:", data["agent_ready_count"])
    print("Gesperrt oder offen:", data["blocked_count"])
    print("TXT:", txt)
    print("CSV:", csv_file)
    print("JSON:", json_file)
    print("Konfiguration:", CONFIG)

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
