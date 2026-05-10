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
LOG = ROOT / "Windows_App" / "Logs"
LIST_DIR = LOG / "Vorzimmer_Arbeitslisten"
DECISION_DIR = LOG / "Vorzimmer_Entscheidungen"
DRAFT_DIR = DECISION_DIR / "Entwuerfe"
OUT_DIR = LOG / "Vorzimmer_Entscheidungsvorschlaege"

def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def newest(base, pattern):
    if not base.exists():
        return None
    files = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def read_csv(path):
    if not path or not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))

def clean(value):
    return str(value or "").strip()

def make_decision_id(index, row):
    intake = clean(row.get("intake_id"))
    base = intake if intake else "OHNE_INTAKE"
    return f"VORSCHLAG_{index:03d}_{base}"

def propose_action(row):
    bereich = clean(row.get("bereich")).lower()
    lage = clean(row.get("lage")).lower()
    hinweis = clean(row.get("hinweis")).lower()

    text = " ".join([bereich, lage, hinweis])

    if bereich == "roh":
        return (
            "ZURUECKSTELLEN",
            "Rohdatei ist noch nicht durch den Produktionslauf geführt. Zuerst Produktionslauf ausführen."
        )

    if bereich == "quarantaene":
        if "aktive" in text or "ausführbar" in text or ".ps1" in text or ".exe" in text:
            return (
                "ABWEISEN",
                "Aktive oder ausführbare Datei bleibt gesperrt. Keine Übernahme in den normalen Bestand."
            )
        return (
            "RUECKFRAGE_ABSENDER",
            "Datei liegt in Quarantäne. Ersatzübersendung oder Klärung beim Absender erforderlich."
        )

    if bereich == "signatur":
        return (
            "SIGNATURPRUEFUNG",
            "Signaturhinweis vorhanden. Signaturprüfung ist vor weiterer Bearbeitung erforderlich."
        )

    if bereich == "sprachpruefung":
        return (
            "SPRACHPRUEFUNG",
            "Sprachprüfung ist offen oder unklar. Sprache und Übersetzungsbedarf manuell festlegen."
        )

    if bereich == "rueckfrage":
        return (
            "RUECKFRAGE_ABSENDER",
            "Rückfrage an den Absender ist organisatorisch offen."
        )

    if bereich == "vorzimmer":
        if "signatur" in text:
            return (
                "SIGNATURPRUEFUNG",
                "Vorzimmerkarte weist auf Signaturprüfung hin."
            )
        if "sprache" in text or "übersetzung" in text or "uebersetzung" in text:
            return (
                "SPRACHPRUEFUNG",
                "Vorzimmerkarte weist auf Sprach- oder Übersetzungsprüfung hin."
            )
        return (
            "ANWALTVORLAGE",
            "Vorzimmerentscheidung offen. Technisch nicht gesperrter Eingang kann dem Anwalt vorgelegt werden."
        )

    if bereich == "geprueft":
        return (
            "ANWALTVORLAGE",
            "Technisch geprüfte Datei liegt bereit. Nächster Schritt ist Anwaltvorlage oder Aktenzuordnung."
        )

    if bereich == "anwalt":
        return (
            "KEINE_AKTION",
            "Datei liegt bereits in Anwaltvorlage."
        )

    if bereich == "abgewiesen":
        return (
            "ARCHIVIEREN",
            "Abgewiesener Eingang kann nach Nachweis archiviert werden."
        )

    return (
        "ZURUECKSTELLEN",
        "Keine sichere automatische Vorschlagsregel vorhanden. Manuelle Prüfung erforderlich."
    )

def main():
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest_list = newest(LIST_DIR, "VORZIMMER_ARBEITSLISTE_V1_*.csv")
    rows = read_csv(latest_list)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    draft_csv = DRAFT_DIR / f"ENTWURF_VORZIMMER_ENTSCHEIDUNG_V1_{ts}.csv"
    report_txt = OUT_DIR / f"VORZIMMER_ENTSCHEIDUNGSVORSCHLAG_V1_{ts}.txt"
    report_json = OUT_DIR / f"VORZIMMER_ENTSCHEIDUNGSVORSCHLAG_V1_{ts}.json"
    report_csv = OUT_DIR / f"VORZIMMER_ENTSCHEIDUNGSVORSCHLAG_V1_{ts}.csv"

    proposals = []

    for index, row in enumerate(rows, start=1):
        action, reason = propose_action(row)

        proposal = {
            "decision_id": make_decision_id(index, row),
            "intake_id": clean(row.get("intake_id")),
            "source_path": clean(row.get("source_path")),
            "aktion": action,
            "begruendung": reason,
            "frist": "",
            "verantwortlich": "Vorzimmer",
            "bereich": clean(row.get("bereich")),
            "lage": clean(row.get("lage")),
            "original_name": clean(row.get("original_name")),
            "hinweis": clean(row.get("hinweis")),
            "nachweise": clean(row.get("nachweise")),
        }

        proposals.append(proposal)

    fields_decision = [
        "decision_id",
        "intake_id",
        "source_path",
        "aktion",
        "begruendung",
        "frist",
        "verantwortlich",
    ]

    with open(draft_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields_decision, delimiter=";")
        writer.writeheader()
        for p in proposals:
            writer.writerow({k: p.get(k, "") for k in fields_decision})

    fields_report = [
        "decision_id",
        "bereich",
        "lage",
        "intake_id",
        "original_name",
        "aktion",
        "begruendung",
        "source_path",
        "nachweise",
    ]

    with open(report_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields_report, delimiter=";")
        writer.writeheader()
        for p in proposals:
            writer.writerow({k: p.get(k, "") for k in fields_report})

    data = {
        "time": now(),
        "latest_arbeitsliste": str(latest_list) if latest_list else "",
        "proposal_count": len(proposals),
        "draft_csv": str(draft_csv),
        "report_txt": str(report_txt),
        "report_csv": str(report_csv),
        "proposals": proposals,
        "warning": "Dieser Entwurf wird nicht automatisch ausgeführt. Zur Ausführung muß er bewußt in den Entscheidungsordner übernommen werden."
    }

    report_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    with open(report_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("VORZIMMER ENTSCHEIDUNGSVORSCHLAG V1\n")
        f.write("=" * 80 + "\n")
        f.write("Zeit: " + data["time"] + "\n")
        f.write("Arbeitsliste: " + data["latest_arbeitsliste"] + "\n")
        f.write("Vorschläge: " + str(len(proposals)) + "\n")
        f.write("Entwurfsdatei: " + str(draft_csv) + "\n\n")
        f.write("WICHTIG\n")
        f.write("-" * 80 + "\n")
        f.write("Die Entwurfsdatei liegt im Ordner Entwuerfe und wird nicht automatisch ausgeführt.\n")
        f.write("Erst nach fachlicher Kontrolle darf sie in den Entscheidungsordner übernommen werden.\n\n")

        if not proposals:
            f.write("Keine offenen Vorzimmerentscheidungen gefunden.\n")
        else:
            for i, p in enumerate(proposals, start=1):
                f.write(str(i) + ". " + p["aktion"] + "\n")
                f.write("-" * 80 + "\n")
                f.write("Bereich: " + p["bereich"] + "\n")
                f.write("Lage: " + p["lage"] + "\n")
                f.write("Intake-ID: " + p["intake_id"] + "\n")
                f.write("Name: " + p["original_name"] + "\n")
                f.write("Quelle: " + p["source_path"] + "\n")
                f.write("Begründung: " + p["begruendung"] + "\n")
                if p["nachweise"]:
                    f.write("Nachweise: " + p["nachweise"] + "\n")
                f.write("\n")

    readme = DRAFT_DIR / "README_ENTWUERFE.txt"
    readme.write_text(
        "Dieser Ordner enthält Entwürfe für Vorzimmerentscheidungen.\n"
        "Dateien in diesem Ordner werden nicht automatisch ausgeführt.\n"
        "Zur Ausführung muß eine geprüfte Entscheidungs-CSV bewußt nach "
        "Windows_App\\Logs\\Vorzimmer_Entscheidungen kopiert werden.\n",
        encoding="utf-8",
        newline="\n"
    )

    print("")
    print("VORZIMMER_ENTSCHEIDUNGSVORSCHLAG_V1 FERTIG")
    print("Offene Vorschläge:", len(proposals))
    print("Arbeitsliste:", latest_list)
    print("Entwurfs-CSV:", draft_csv)
    print("Bericht TXT:", report_txt)
    print("Bericht CSV:", report_csv)
    print("Bericht JSON:", report_json)

    if proposals:
        print("")
        print("VORSCHLÄGE:")
        for p in proposals:
            print(p["aktion"], "|", p["bereich"], "|", p["original_name"])

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
