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
        "legal_context": "schwedisches Arbeitsrecht und schwedische Verfahrenslogik",
        "internal_work_language": "de",
        "principle": "Der einzige systematische Sprachunterschied ist Deutsch als interne Arbeitssprache des bearbeitenden Anwalts."
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
    ],
    "principle": "Fallbezogene Dokumente werden im Posteingang nicht inhaltlich bewertet. Sie werden als unbewertetes Aktenmaterial geführt, bis nachgelagerte Agentenbearbeitung oder anwaltliche Bearbeitung sie zuordnet."
}

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)
        keep = path / ".gitkeep"
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

def boundary(area):
    mapping = {
        "roh": (
            "ROH_EINGANG",
            "Produktionslauf starten",
            False,
            "Rohdatei ist noch nicht technisch geprüft."
        ),
        "quarantaene": (
            "TECHNISCH_GESPERRT_ODER_UNKLAR",
            "technische Nachprüfung, Rückfrage oder Zurückweisung",
            False,
            "Datei darf inhaltlich nicht bearbeitet werden, solange technische Sperre oder Unklarheit besteht."
        ),
        "signatur": (
            "SIGNATURPRUEFUNG_OFFEN",
            "Signaturprüfung oder Absenderprüfung",
            False,
            "Signaturhinweis ist vorrangig. Inhaltliche Agentenbearbeitung erst nach Signaturentscheidung."
        ),
        "sprachpruefung": (
            "SPRACHKONTEXT_ODER_UEBERSETZUNG_OFFEN",
            "Sprache festlegen oder Übersetzung vorbereiten",
            False,
            "Sprachliche Unklarheit muß vor tiefer Inhaltsbearbeitung geklärt werden."
        ),
        "geprueft": (
            "TECHNISCH_FREIGEGEBEN_UNBEWERTETES_AKTENMATERIAL",
            "Anwaltvorlage oder nachgelagerte Agentenbearbeitung",
            True,
            "Die Datei ist nicht als Beweis, Entlastung oder Aussage bewertet. Sie ist nur technisch freigegebenes Aktenmaterial."
        ),
        "vorzimmer": (
            "VORZIMMERENTSCHEIDUNG_OFFEN",
            "organisatorische Entscheidung",
            False,
            "Vorzimmerkarten steuern nur den nächsten organisatorischen Schritt."
        ),
        "anwalt": (
            "ANWALTVORLAGE_UNBEWERTETES_AKTENMATERIAL",
            "anwaltliche oder agentengestützte Aktenbearbeitung",
            True,
            "Erst hier darf die inhaltliche Zuordnung vorbereitet werden."
        ),
        "rueckfrage": (
            "RUECKFRAGE_OFFEN",
            "Absender anschreiben oder Ersatzübersendung verlangen",
            False,
            "Der Eingang ist organisatorisch noch nicht verwertbar."
        ),
        "abgewiesen": (
            "ABGEWIESEN",
            "Archivierung oder Nachweis",
            False,
            "Abgewiesener Eingang wird nicht inhaltlich bearbeitet."
        ),
    }

    status, next_step, allowed, reason = mapping.get(area, (
        "UNBEKANNT",
        "Vorzimmer prüfen",
        False,
        "Bereich nicht eindeutig geregelt."
    ))

    return {
        "posteingang_status": status,
        "allowed_next_step": next_step,
        "agent_review_allowed": allowed,
        "reason": reason
    }

def build_rows():
    rows = []

    for area in WORK_KEYS:
        for file in active_files(DIRS[area]):
            b = boundary(area)
            rows.append({
                "time": now(),
                "area": area,
                "intake_id": extract_intake_id(file),
                "original_name": file.name,
                "path": str(file),
                "posteingang_status": b["posteingang_status"],
                "allowed_next_step": b["allowed_next_step"],
                "agent_review_allowed": str(b["agent_review_allowed"]),
                "content_classification_allowed_in_posteingang": "False",
                "content_classification": "UNBEWERTETES_AKTENMATERIAL",
                "forbidden_labels_here": "BEWEIS | ENTLASTUNG | AUSSAGE | NACHWEIS | SACHVERHALTSBLOCK | RECHTLICHE_RELEVANZ",
                "downstream_responsibility": "Nachgelagerte Agentenbearbeitung oder anwaltliche Bearbeitung",
                "reason": b["reason"],
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
        "rows": rows
    }

    json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    CONFIG.write_text(json.dumps(CONFIG_DATA, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    fields = [
        "time",
        "area",
        "intake_id",
        "original_name",
        "path",
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
        f.write("Schwedischer Arbeitsrechtsstreit zwischen Arbeitnehmer und kommunalem Arbeitgeber.\n")
        f.write("Amtssprache: Schwedisch.\n")
        f.write("Prozeßsprache: Schwedisch.\n")
        f.write("Maßgebliche Verfahrenslogik: schwedisches Arbeitsrecht und schwedisches Verfahren.\n")
        f.write("Interne Arbeitssprache des bearbeitenden Anwalts: Deutsch.\n\n")

        f.write("GRENZE DES POSTEINGANGS\n")
        f.write("-" * 80 + "\n")
        f.write("Der Posteingang bewertet keine Beweise, keine Entlastung und keine Aussagen.\n")
        f.write("Der Posteingang prüft nur Eingang, Sicherheit, Signaturhinweis, Sprache und organisatorische Weiterleitung.\n")
        f.write("Die inhaltliche Einordnung erfolgt nachgelagert durch Agenten oder anwaltliche Bearbeitung.\n\n")

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
                f.write("Grund: " + row["reason"] + "\n\n")

    return txt, csv_file, json_file

def main():
    ensure_dirs()
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
