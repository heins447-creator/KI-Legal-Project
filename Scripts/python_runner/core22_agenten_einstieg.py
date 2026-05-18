"""
CORE-22 – Agenten-Einstieg und Arbeitsregel-Erzwingung
Prüft vor jedem Auftrag:
  1. Arbeitsindex vorhanden?
  2. Startpunkt vorhanden?
  3. Arbeitsbereich freigegeben?
  4. Pfad gesperrt oder nur Referenz?
  5. Schreibzugriff erlaubt?
Erzeugt: Regeldatei für Roo + Bericht
"""
import json
import os
import sys
import datetime
from pathlib import Path

BERICHT_PFAD = "ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt"
REGEL_PFAD = "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json"
KONFIG_PFAD = "Config/core21_arbeitsindex_v1.json"

def log(msg):
    ts = datetime.datetime.now().isoformat()
    print(f"[CORE-22] {msg}")
    return f"[{ts}] {msg}"

def lade_konfig():
    if not os.path.exists(KONFIG_PFAD):
        return None, f"Konfiguration fehlt: {KONFIG_PFAD}"
    with open(KONFIG_PFAD, "r", encoding="utf-8") as f:
        return json.load(f), None

def pruefe_startpunkt(konfig):
    start = konfig.get("arbeitsmodus", {}).get("empfohlener_start", "")
    if not start:
        return False, "Kein empfohlener_start in Konfiguration"
    if not os.path.exists(start):
        return False, f"Startpunkt fehlt: {start}"
    return True, f"Startpunkt OK: {start}"

def pruefe_erste_lese_dateien(konfig):
    dateien = konfig.get("arbeitsmodus", {}).get("erste_lese_dateien", [])
    fehlend = [d for d in dateien if not os.path.exists(d)]
    if fehlend:
        return False, f"Erste Lesedateien fehlen: {fehlend}"
    return True, f"Erste Lesedateien OK ({len(dateien)} Dateien)"

def bereich_status(konfig, pfad):
    """
    Gibt Status für einen Pfad zurück:
    'aktiv'      → darf bearbeitet werden
    'referenz'   → nur lesen, nicht schreiben
    'gesperrt'   → nicht bearbeiten
    'unbekannt'  → nicht in Index, Vorsicht
    """
    bereiche = konfig.get("bereiche", {})
    aktiv = bereiche.get("aktiv", [])
    referenz = bereiche.get("referenz", [])
    gesperrt_kategorien = bereiche.get("gesperrt", [])

    # Prüfe ob Pfad unter aktiv fällt
    for a in aktiv:
        if pfad.startswith(a) or pfad == a.rstrip("/"):
            return "aktiv"

    # Prüfe ob Pfad unter referenz fällt
    for r in referenz:
        if pfad.startswith(r) or pfad == r.rstrip("/"):
            return "referenz"

    # Prüfe ob Pfad gesperrte Kategorie im Namen hat
    for g in gesperrt_kategorien:
        if g.lower() in pfad.lower():
            return "gesperrt"

    return "unbekannt"

def darf_schreiben(konfig, pfad):
    status = bereich_status(konfig, pfad)
    if status == "aktiv":
        return True, "aktiv"
    if status == "referenz":
        return False, "referenz: nur lesen"
    if status == "gesperrt":
        return False, "gesperrt: keine Bearbeitung"
    return False, "unbekannt – nicht in Arbeitsindex"

def erzeuge_regeln(konfig):
    aktiv = konfig.get("bereiche", {}).get("aktiv", [])
    referenz = konfig.get("bereiche", {}).get("referenz", [])
    gesperrt = konfig.get("bereiche", {}).get("gesperrt", [])
    start = konfig.get("arbeitsmodus", {}).get("empfohlener_start", "")
    lese_dateien = konfig.get("arbeitsmodus", {}).get("erste_lese_dateien", [])
    skript_prio = konfig.get("skript_prioritaet", [])

    regeln = {
        "meta": {
            "modul_id": "CORE-22",
            "name": "Agenten-Einstieg und Arbeitsregel-Erzwingung",
            "version": "1.0.0",
            "zeitstempel": datetime.datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_regelnd": True
        },
        "agenten_einstieg": {
            "pfad_zu_arbeitsindex": KONFIG_PFAD,
            "pfad_zu_regeldatei": REGEL_PFAD,
            "start_datei": start,
            "erste_lese_dateien": lese_dateien
        },
        "arbeitsregeln": {
            "vor_jedem_auftrag": [
                "1. Arbeitsindex vorhanden prüfen",
                "2. Startpunkt vorhanden prüfen",
                "3. Zielpfad in bereich_status() prüfen",
                "4. Bei 'aktiv' → Schreiben erlaubt",
                "5. Bei 'referenz' → NUR lesen, NICHT schreiben",
                "6. Bei 'gesperrt' → ABLEHNEN",
                "7. Bei 'unbekannt' → NACHFRAGEN oder als Archiv behandeln"
            ],
            "schreibregeln": {
                "erlaubt_in": aktiv,
                "verboten_in": referenz + gesperrt,
                "exception_nur_mit_freigabe": True
            },
            "leseregeln": {
                "erlaubt_in": aktiv + referenz,
                "gesperrte_nur_mit_freigabe": gesperrt
            },
            "skript_prioritaet": skript_prio
        },
        "verbotene_operationen": [
            "Löschen im Altbestand",
            "Verschieben im Altbestand",
            "Umbenennen im Altbestand",
            "Schreiben in referenz/ oder gesperrt/",
            "Echte Mandantendaten an externe Modelle",
            "API-Schlüssel in Git"
        ],
        "erlaubte_operationen": [
            "Lesen in aktiv/ und referenz/",
            "Schreiben in aktiv/",
            "Kopierende Migration (nur wenn Dry-Run freigegeben)",
            "Berichte in Reports/ schreiben",
            "Pläne in 08_Migration/01_Plaene/ schreiben",
            "Manifeste in 08_Migration/09_Manifest/ schreiben"
        ],
        "entscheidungsbaum": {
            "auftrag_betrifft_altbestand": {
                "beschreibung": "Altbestand = Pfade außerhalb ALIN_Neustart_Core/",
                "aktion": "ABLEHNEN oder als referenz behandeln"
            },
            "auftrag_betrifft_neustart_core": {
                "beschreibung": "Pfad beginnt mit ALIN_Neustart_Core/",
                "aktion": "bereich_status() prüfen, dann entscheiden"
            },
            "pfad_ist_aktiv": {
                "beschreibung": "bereich_status() == 'aktiv'",
                "aktion": "SCHREIBEN ERLAUBT"
            },
            "pfad_ist_referenz": {
                "beschreibung": "bereich_status() == 'referenz'",
                "aktion": "NUR LESEN, NICHT SCHREIBEN"
            },
            "pfad_ist_gesperrt": {
                "beschreibung": "bereich_status() == 'gesperrt'",
                "aktion": "ABLEHNEN"
            }
        }
    }
    return regeln

def schreibe_json(data, pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return pfad

def schreibe_bericht(zeilen, pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-22 AGENTEN-EINSTIEG-BERICHT\n")
        f.write("=" * 70 + "\n\n")
        for z in zeilen:
            f.write(z + "\n")
        f.write("\n" + "=" * 70 + "\n")
        f.write("CORE-22 ABGESCHLOSSEN\n")
    return pfad

def main():
    zeilen = []
    zeilen.append(log("Starte CORE-22 Agenten-Einstieg"))

    # 1. Konfiguration laden
    konfig, err = lade_konfig()
    if err:
        zeilen.append(log(f"FEHLER: {err}"))
        schreibe_bericht(zeilen, BERICHT_PFAD)
        return 1
    zeilen.append(log("Konfiguration geladen"))

    # 2. Startpunkt prüfen
    ok, msg = pruefe_startpunkt(konfig)
    zeilen.append(log(msg))
    if not ok:
        schreibe_bericht(zeilen, BERICHT_PFAD)
        return 1

    # 3. Erste Lesedateien prüfen
    ok, msg = pruefe_erste_lese_dateien(konfig)
    zeilen.append(log(msg))
    if not ok:
        schreibe_bericht(zeilen, BERICHT_PFAD)
        return 1

    # 4. Regeln erzeugen
    regeln = erzeuge_regeln(konfig)
    schreibe_json(regeln, REGEL_PFAD)
    zeilen.append(log(f"Regeln geschrieben: {REGEL_PFAD}"))

    # 5. Beispiel-Prüfungen durchführen
    test_pfade = [
        "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
        "ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.json",
        "ALIN_Neustart_Core/08_Migration/04_Gesperrt/somefile.txt",
        "Scripts/python_runner/core22_agenten_einstieg.py",
        "Projektplanung/CORE22_AGENTEN_EINSTIEG.md",
        "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_modulkarte.json",
    ]
    for tp in test_pfade:
        status = bereich_status(konfig, tp)
        darf, grund = darf_schreiben(konfig, tp)
        zeilen.append(log(f"Test: {tp} -> Status={status}, Schreiben={darf} ({grund})"))

    # 6. Zusammenfassung
    zeilen.append(log("=" * 60))
    zeilen.append(log("ZUSAMMENFASSUNG"))
    zeilen.append(log("=" * 60))
    zeilen.append(log("Arbeitsindex: OK"))
    zeilen.append(log("Startpunkt: OK"))
    zeilen.append(log("Regeldatei: OK"))
    zeilen.append(log("Agenten-Einstieg: FREIGEGEBEN"))
    zeilen.append(log("=" * 60))
    zeilen.append(log("CORE-22 ABGESCHLOSSEN"))

    schreibe_bericht(zeilen, BERICHT_PFAD)
    return 0

if __name__ == "__main__":
    sys.exit(main())
