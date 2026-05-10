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
OUT = LOG / "Aktenmaterial_Agentenabgrenzung"
CONFIG = ROOT / "Config" / "posteingang_aktenmaterial_agentenabgrenzung_v1.json"

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
    "geprueft",
    "vorzimmer",
    "anwalt",
    "rueckfrage",
    "abgewiesen",
    "signatur",
    "sprachpruefung",
]

IGNORE = {".gitkeep", "README_POSTEINGANG.md"}

CONFIG_DATA = {
    "version": "V1",
    "case_context": {
        "case_type": "Schwedischer Arbeitsrechtsstreit",
        "parties": "Arbeitnehmer gegen kommunalen Arbeitgeber",
        "official_language": "sv",
        "procedural_language": "sv",
        "internal_work_language": "de",
        "rule": "Alle fallbezogenen Dokumente bleiben im Posteingang unbewertetes Aktenmaterial."
    },
    "posteingang_may_decide": [
        "Eingang erfassen",
        "Hashwert bilden",
        "Dateityp prüfen",
        "aktive oder ausführbare Dateien sperren",
        "Windows-Defender-Prüfung anstoßen",
        "Signaturhinweise erkennen",
        "Sprachkontext feststellen",
        "Vorzimmerentscheidung vorbereiten",
        "technisch freigegebene Dateien organisatorisch weiterleiten"
    ],
    "posteingang_must_not_decide": [
        "Beweiswert",
        "Entlastungswert",
        "Aussagequalität",
        "Zeugenbezug",
        "rechtliche Relevanz",
        "prozessuale Verwendbarkeit",
        "Sachverhaltsblock",
        "Angriffs- oder Verteidigungsmittel",
        "endgültige Aktenzuordnung"
    ],
    "downstream_agent_tasks": [
        "Dokumentart bestimmen",
        "Beweis oder Entlastung erkennen",
        "Aussage, Nachweis, Korrespondenz oder Kontextmaterial trennen",
        "Sachverhaltsblock zuordnen",
        "Verfahrensrolle zuordnen",
        "rechtliche Relevanz vorbereiten",
        "Übersetzungsbedarf konkretisieren",
        "Anwaltvorlage fachlich strukturieren"
    ]
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
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

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def boundary_for(area, file):
    if area == "roh":
        return {
            "posteingang_status": "ROH_EINGANG",
            "allowed_next_step": "Produktionslauf starten",
            "agent_review_allowed": False,
            "reason": "Rohdatei ist noch nicht technisch geprüft."
        }

    if area == "quarantaene":
        return {
            "posteingang_status": "TECHNISCH_GESPERRT_ODER_UNKLAR",
            "allowed_next_step": "technische Nachprüfung, Rückfrage oder Zurückweisung",
            "agent_review_allowed": False,
            "reason": "Datei darf inhaltlich nicht bearbeitet werden, solange technische Sperre oder Unklarheit besteht."
        }

    if area == "signatur":
        return {
            "posteingang_status": "SIGNATURPRUEFUNG_OFFEN",
            "allowed_next_step": "Signaturprüfung oder Absenderprüfung",
            "agent_review_allowed": False,
            "reason": "Signaturhinweis ist vorrangig. Inhaltliche Agentenbearbeitung erst nach Signaturentscheidung."
        }

    if area == "sprachpruefung":
        return {
            "posteingang_status": "SPRACHKONTEXT_ODER_UEBERSETZUNG_OFFEN",
            "allowed_next_step": "Sprache festlegen oder Übersetzung vorbereiten",
            "agent_review_allowed": False,
            "reason": "Sprachliche Unklarheit muß vor tiefer Inhaltsbearbeitung geklärt werden."
        }

    if area == "geprueft":
        return {
            "posteingang_status": "TECHNISCH_FREIGEGEBEN_UNBEWERTETES_AKTENMATERIAL",
            "allowed_next_step": "Anwaltvorlage oder nachgelagerte Agentenbearbeitung",
            "agent_review_allowed": True,
            "reason": "Die Datei ist nicht als Beweis, Entlastung oder Aussage bewertet. Sie ist nur technisch freigegebenes Aktenmaterial."
        }

    if area == "vorzimmer":
        return {
            "posteingang_status": "VORZIMMERENTSCHEIDUNG_OFFEN",
            "allowed_next_step": "organisatorische Entscheidung",
            "agent_review_allowed": False,
            "reason": "Vorzimmerkarte steuert nur den nächsten organisatorischen Schritt."
        }

    if area == "anwalt":
        return {
            "posteingang_status": "ANWALTVORLAGE_UNBEWERTETES_AKTENMATERIAL",
            "allowed_next_step": "anwaltliche oder agentengestützte Aktenbearbeitung",
            "agent_review_allowed": True,
            "reason": "Erst hier darf die inhaltliche Zuordnung vorbereitet werden."
        }

    if area == "rueckfrage":
        return {
            "posteingang_status": "RUECKFRAGE_OFFEN",
            "allowed_next_step": "Absender anschreiben oder Ersatzübersendung verlangen",
            "agent_review_allowed": False,
            "reason": "Der Eingang ist organisatorisch noch nicht verwertbar."
        }

    if area == "abgewiesen":
        return {
            "posteingang_status": "ABGEWIESEN",
            "allowed_next_step": "Archivierung oder Nachweis",
            "agent_review_allowed": False,
            "reason": "Abgewiesener Eingang wird nicht inhaltlich bearbeitet."
        }

    return {
        "posteingang_status": "UNBEKANNT",
        "allowed_next_step": "Vorzimmer prüfen",
        "agent_review_allowed": False,
        "reason": "Bereich nicht eindeutig geregelt."
    }

def build_rows():
    rows = []

    for area in WORK_KEYS:
        for file in active_files(DIRS[area]):
            intake_id = extract_intake_id(file)
            data = read_json(file) if file.suffix.lower() == ".json" else {}
            boundary = boundary_for(area, file)

            original_name = data.get("original_name") or file.name
            stored_path = data.get("stored_path") or str(file)

            rows.append({
                "time": now(),
                "area": area,
                "intake_id": intake_id,
                "original_name": original_name,
                "path": str(file),
                "stored_path": stored_path,
                "posteingang_status": boundary["posteingang_status"],
                "allowed_next_step": boundary["allowed_next_step"],
                "agent_review_allowed": str(boundary["agent_review_allowed"]),
                "content_classification_allowed_in_posteingang": "False",
                "content_classification": "UNBEWERTETES_AKTENMATERIAL",
                "forbidden_labels_here": "BEWEIS | ENTLASTUNG | AUSSAGE | NACHWEIS | SACHVERHALTSBLOCK | RECHTLICHE_RELEVANZ",
                "downstream_responsibility": "Nachgelagerte Agentenbearbeitung oder anwaltliche Bearbeitung",
                "reason": boundary["reason"],
            })

    rows.sort(key=lambda x: (x["area"], x["original_name"]))
    return rows

def write_reports(rows):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    txt = OUT / f"POSTEINGANG_AKTENMATERIAL_AGENTENABGRENZUNG_V1_{ts}.txt"
    csv_file = OUT / f"POSTEINGANG_AKTENMATERIAL_AGENTENABGRENZUNG_V1_{ts}.csv"
    json_file = OUT / f"POSTEINGANG_AKTENMATERIAL_AGENTENABGRENZUNG_V1_{ts}.json"

    payload = {
        "time": now(),
        "rows_count": len(rows),
        "config": CONFIG_DATA,
        "rows": rows,
        "principle": "Der Posteingang bewertet keine Beweise, keine Entlastung und keine Aussagen. Er führt fallbezogene Dokumente nur als unbewertetes Aktenmaterial weiter."
    }

    json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "time",
        "area",
        "intake_id",
        "original_name",
        "path",
        "stored_path",
        "posteingang_status",
        "allowed_next_step",
        "agent_review_allowed",
        "content_classification_allowed_in_posteingang",
        "content_classification",
        "forbidden_labels_here",
        "downstream_responsibility",
        "reason",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    with open(txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("POSTEINGANG AKTENMATERIAL AGENTENABGRENZUNG V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + now() + "\n")
        f.write("Einträge: " + str(len(rows)) + "\n\n")

        f.write("FALLKONTEXT\n")
        f.write("-" * 80 + "\n")
        f.write("Schwedischer Arbeitsrechtsstreit: Arbeitnehmer gegen kommunalen Arbeitgeber.\n")
        f.write("Amtssprache: Schwedisch.\n")
        f.write("Prozeßsprache: Schwedisch.\n")
        f.write("Interne Arbeitssprache des bearbeitenden Anwalts: Deutsch.\n\n")

        f.write("GRENZE DES POSTEINGANGS\n")
        f.write("-" * 80 + "\n")
        f.write("Der Posteingang bewertet nicht, ob ein Dokument Beweis, Entlastung, Aussage oder Nachweis ist.\n")
        f.write("Diese Einordnung erfolgt erst nachgelagert durch Agenten oder anwaltliche Bearbeitung.\n")
        f.write("Der Posteingang prüft nur Eingang, Sicherheit, Signaturhinweis, Sprache und organisatorische Weiterleitung.\n\n")

        if not rows:
            f.write("Keine aktiven Arbeitsdateien vorhanden.\n")
        else:
            f.write("AKTIVE ARBEITSDATEIEN\n")
            f.write("-" * 80 + "\n")
            for row in rows:
                f.write(row["area"] + " | " + row["intake_id"] + "\n")
                f.write("Name: " + row["original_name"] + "\n")
                f.write("Status: " + row["posteingang_status"] + "\n")
                f.write("Klassifikation im Posteingang: " + row["content_classification"] + "\n")
                f.write("Nächster Schritt: " + row["allowed_next_step"] + "\n")
                f.write("Begründung: " + row["reason"] + "\n\n")

    return txt, csv_file, json_file

def main():
    ensure_dirs()
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    rows = build_rows()
    txt, csv_file, json_file = write_reports(rows)

    print("")
    print("POSTEINGANG_AKTENMATERIAL_AGENTENABGRENZUNG_V1 FERTIG")
    print("Einträge:", len(rows))
    print("Konfiguration:", CONFIG)
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
