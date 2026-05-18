#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-19 – Reste-/Archiv-/Sperrplan
Erstellt Plaene fuer nicht-kopierte Dateien: Reste, Archiv, Sperren.
Nur planend. Keine Dateien werden kopiert, verschoben, geloescht oder umbenannt.
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
AUSWERTUNG_PFAD = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE14_auswertung.json")
MANIFEST_PFAD = os.path.join(ALIN_CORE, "08_Migration", "09_Manifest", "CORE17_kopierte_dateien_manifest.json")
AUSGABE_DIR = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE19_RESTE_ARCHIV_SPERRPLAN_BERICHT.txt")


def log(msg):
    print(f"[CORE-19] {msg}")


def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def erstelle_reste_plan(auswertungen, kopierte_pfade):
    reste = []
    archiv = []
    gesperrt = []
    testreste = []
    laufzeit = []
    dubletten = []
    manuell = []

    for a in auswertungen:
        rel = a.get("relativer_pfad", "")
        ziel = a.get("zielentscheidung", "")

        # Bereits kopiert?
        if rel in kopierte_pfade:
            continue

        eintrag = {
            "relativer_pfad": rel,
            "dateiname": a.get("dateiname", ""),
            "dateigroesse": a.get("dateigroesse", 0),
            "sha256": a.get("sha256", ""),
            "klassifikation": a.get("klassifikation", ""),
            "zielentscheidung": ziel,
            "begruendung": a.get("begruendung", ""),
            "gesperrt": a.get("gesperrt", False),
        }

        if ziel == "SPERREN_NICHT_KOPIEREN":
            gesperrt.append(eintrag)
        elif ziel == "ARCHIV_VORSCHLAG":
            archiv.append(eintrag)
        elif ziel == "TESTREST_NICHT_KOPIEREN":
            testreste.append(eintrag)
        elif ziel == "LAUFZEITARTEFAKT_NICHT_KOPIEREN":
            laufzeit.append(eintrag)
        elif ziel == "DUBLETTE_NICHT_KOPIEREN":
            dubletten.append(eintrag)
        elif ziel == "MANUELL_PRUEFEN":
            manuell.append(eintrag)
        elif ziel == "CONFIG_LOKAL_MANUELL":
            manuell.append(eintrag)
        elif ziel == "NICHT_UEBERNEHMEN_ERSETZT":
            archiv.append(eintrag)
        else:
            reste.append(eintrag)

    return {
        "reste": reste,
        "archiv": archiv,
        "gesperrt": gesperrt,
        "testreste": testreste,
        "laufzeit": laufzeit,
        "dubletten": dubletten,
        "manuell": manuell,
    }


def schreibe_json(plaene, statistik):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE19_reste_archiv_sperrplan.json")
    out = {
        "meta": {
            "modul_id": "CORE-19",
            "name": "Reste-/Archiv-/Sperrplan",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_planend": True,
        },
        "zusammenfassung": statistik,
        "plaene": plaene,
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"JSON geschrieben: {pfad}")
    return pfad


def schreibe_bericht(plaene, statistik):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-19 RESTE-/ARCHIV-/SPERRPLAN BERICHT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n\n")
        f.write("Zusammenfassung:\n")
        f.write("-" * 40 + "\n")
        for kategorie, anzahl in sorted(statistik.items()):
            f.write(f"  {kategorie:<30} {anzahl:>6}\n")
        f.write("\n")

        for kategorie, eintraege in plaene.items():
            if eintraege:
                f.write(f"{kategorie.upper()} ({len(eintraege)} Eintraege):\n")
                f.write("-" * 40 + "\n")
                for e in eintraege[:10]:
                    f.write(f"  {e['relativer_pfad']}\n")
                if len(eintraege) > 10:
                    f.write(f"  ... und {len(eintraege) - 10} weitere\n")
                f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("ENDE BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def hauptlauf():
    log("Starte CORE-19 Reste-/Archiv-/Sperrplan...")

    if not os.path.exists(AUSWERTUNG_PFAD):
        log(f"FEHLER: Auswertung nicht gefunden: {AUSWERTUNG_PFAD}")
        global FEHLER
        FEHLER += 1
        return

    log(f"Lade Auswertung: {AUSWERTUNG_PFAD}")
    auswertung = lade_json(AUSWERTUNG_PFAD)
    auswertungen = auswertung.get("auswertungen", [])
    log(f"Auswertung geladen: {len(auswertungen)} Dateien")

    # Lade kopierte Pfade aus Manifest
    kopierte_pfade = set()
    if os.path.exists(MANIFEST_PFAD):
        manifest = lade_json(MANIFEST_PFAD)
        for e in manifest.get("kopierte_dateien", []):
            kopierte_pfade.add(e.get("relativer_pfad", ""))
        log(f"Manifest geladen: {len(kopierte_pfade)} kopierte Dateien")
    else:
        log("WARNUNG: Manifest nicht gefunden. Alle Dateien als nicht-kopiert betrachtet.")
        global WARNUNGEN
        WARNUNGEN += 1

    log("Erstelle Plaene...")
    plaene = erstelle_reste_plan(auswertungen, kopierte_pfade)

    statistik = {k: len(v) for k, v in plaene.items()}

    schreibe_json(plaene, statistik)
    schreibe_bericht(plaene, statistik)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    for kategorie, anzahl in sorted(statistik.items()):
        log(f"  {kategorie:<30} {anzahl:>6}")
    log("=" * 60)
    log("CORE-19 RESTE-/ARCHIV-/SPERRPLAN ABGESCHLOSSEN")


def selbsttest():
    print("CORE-19 SELBSTTEST =====================================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    def t(bez, bed):
        global FEHLER
        if not bed:
            print(f"  [FAIL] {bez}")
            FEHLER += 1
        else:
            print(f"  [OK]   {bez}")

    t("Projektwurzel existiert", os.path.isdir(PROJEKT_WURZEL))

    # Test erstelle_reste_plan
    test_ausw = [
        {"relativer_pfad": "a.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND", "dateiname": "a.py", "dateigroesse": 100, "sha256": "abc", "klassifikation": "AKTIV", "begruendung": "", "gesperrt": False},
        {"relativer_pfad": "b.py", "zielentscheidung": "DUBLETTE_NICHT_KOPIEREN", "dateiname": "b.py", "dateigroesse": 100, "sha256": "def", "klassifikation": "DUBLETTE", "begruendung": "", "gesperrt": False},
        {"relativer_pfad": "c.py", "zielentscheidung": "SPERREN_NICHT_KOPIEREN", "dateiname": "c.py", "dateigroesse": 100, "sha256": "ghi", "klassifikation": "SPERREN", "begruendung": "", "gesperrt": True},
    ]
    plaene = erstelle_reste_plan(test_ausw, {"a.py"})
    t("Kopierte ausgeschlossen", len(plaene["reste"]) == 0)
    t("Dublette erkannt", len(plaene["dubletten"]) == 1)
    t("Gesperrt erkannt", len(plaene["gesperrt"]) == 1)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
