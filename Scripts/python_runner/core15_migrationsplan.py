#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-15 – Migrationsplan mit Zielpfaden
Erstellt fuer jede UEBERNEHMEN_KOPIEREND-Datei einen Zielpfad unter 08_Migration/02_Kopierte_Dateien.
Nur planend. Keine Dateien werden kopiert, verschoben, geloescht oder umbenannt.
"""

import json
import csv
import os
import sys
from datetime import datetime
from collections import defaultdict

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
AUSWERTUNG_PFAD = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE14_auswertung.json")
AUSGABE_DIR = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE15_MIGRATIONSPLAN_BERICHT.txt")
ZIEL_BASIS = os.path.join(ALIN_CORE, "08_Migration", "02_Kopierte_Dateien")

ZIEL_MAPPING = {
    "UEBERNEHMEN_KOPIEREND": "02_Kopierte_Dateien",
    "MANUELL_PRUEFEN": "03_Manuell_Pruefen",
    "SPERREN_NICHT_KOPIEREN": "04_Gesperrt",
    "DUBLETTE_NICHT_KOPIEREN": "05_Dubletten",
    "TESTREST_NICHT_KOPIEREN": "06_Testreste",
    "LAUFZEITARTEFAKT_NICHT_KOPIEREN": "07_Laufzeit_Artefakte",
    "ARCHIV_VORSCHLAG": "08_Archiv_Vorschlag",
    "NICHT_UEBERNEHMEN_ERSETZT": "08_Archiv_Vorschlag",
    "CONFIG_LOKAL_MANUELL": "03_Manuell_Pruefen",
}


def log(msg):
    print(f"[CORE-15] {msg}")


def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def berechne_zielpfad(rel_pfad, zielentscheidung):
    """
    Berechnet den Zielpfad fuer eine Datei im Migrationsplan.
    Behaelt die relative Verzeichnisstruktur bei.
    """
    ziel_ordner = ZIEL_MAPPING.get(zielentscheidung, "03_Manuell_Pruefen")
    ziel_basis = os.path.join(ALIN_CORE, "08_Migration", ziel_ordner)
    return os.path.join(ziel_basis, rel_pfad).replace("\\", "/")


def erstelle_migrationsplan(auswertungen):
    plaene = []
    statistik = defaultdict(int)
    konflikte = []
    zielpfade = set()

    for a in auswertungen:
        rel_pfad = a.get("relativer_pfad", "")
        ziel = a.get("zielentscheidung", "MANUELL_PRUEFEN")
        ziel_pfad = berechne_zielpfad(rel_pfad, ziel)

        # Konfliktpruefung: gleicher Zielpfad
        if ziel_pfad in zielpfade:
            konflikte.append({
                "relativer_pfad": rel_pfad,
                "ziel_pfad": ziel_pfad,
                "grund": "Zielpfad-Kollision",
            })
        else:
            zielpfade.add(ziel_pfad)

        plan = {
            "relativer_pfad": rel_pfad,
            "dateiname": a.get("dateiname", ""),
            "dateiendung": a.get("dateiendung", ""),
            "dateigroesse": a.get("dateigroesse", 0),
            "sha256": a.get("sha256", ""),
            "klassifikation": a.get("klassifikation", ""),
            "zielentscheidung": ziel,
            "ziel_pfad": ziel_pfad,
            "ziel_ordner": ZIEL_MAPPING.get(ziel, "03_Manuell_Pruefen"),
            "kopieren": ziel == "UEBERNEHMEN_KOPIEREND",
            "gesperrt": a.get("gesperrt", False),
            "begruendung": a.get("begruendung", ""),
        }
        plaene.append(plan)
        statistik[ziel] += 1

    return plaene, dict(statistik), konflikte


def schreibe_json(plaene, statistik, konflikte):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE15_migrationsplan.json")
    out = {
        "meta": {
            "modul_id": "CORE-15",
            "name": "Migrationsplan mit Zielpfaden",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_planend": True,
        },
        "zusammenfassung": {
            "anzahl_dateien": len(plaene),
            "zielentscheidungen": statistik,
            "anzahl_konflikte": len(konflikte),
            "kopierende_dateien": statistik.get("UEBERNEHMEN_KOPIEREND", 0),
        },
        "konflikte": konflikte,
        "plaene": plaene,
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"JSON geschrieben: {pfad}")
    return pfad


def schreibe_csv(plaene, statistik=None, konflikte=None):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE15_migrationsplan.csv")
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "relativer_pfad", "dateiname", "dateiendung", "dateigroesse",
                "sha256", "klassifikation", "zielentscheidung", "ziel_pfad",
                "ziel_ordner", "kopieren", "gesperrt", "begruendung",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        for p in plaene:
            row = dict(p)
            row["kopieren"] = str(row["kopieren"])
            row["gesperrt"] = str(row["gesperrt"])
            writer.writerow(row)
    log(f"CSV geschrieben: {pfad}")
    return pfad


def schreibe_bericht(plaene, statistik, konflikte):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-15 MIGRATIONSPLAN BERICHT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        f.write(f"Gesamtdateien: {len(plaene)}\n")
        f.write(f"Konflikte: {len(konflikte)}\n")
        f.write(f"Kopierende Dateien: {statistik.get('UEBERNEHMEN_KOPIEREND', 0)}\n\n")
        f.write("Zielentscheidungen:\n")
        f.write("-" * 40 + "\n")
        for ziel, anzahl in sorted(statistik.items()):
            f.write(f"  {ziel:<45} {anzahl:>6}\n")
        if konflikte:
            f.write("\nKONFLIKTE:\n")
            f.write("-" * 40 + "\n")
            for k in konflikte[:20]:
                f.write(f"  {k['relativer_pfad']} -> {k['ziel_pfad']}\n")
            if len(konflikte) > 20:
                f.write(f"  ... und {len(konflikte) - 20} weitere\n")
        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("ENDE BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def hauptlauf():
    log("Starte CORE-15 Migrationsplan...")

    if not os.path.exists(AUSWERTUNG_PFAD):
        log(f"FEHLER: Auswertung nicht gefunden: {AUSWERTUNG_PFAD}")
        global FEHLER
        FEHLER += 1
        return

    log(f"Lade Auswertung: {AUSWERTUNG_PFAD}")
    auswertung = lade_json(AUSWERTUNG_PFAD)
    auswertungen = auswertung.get("auswertungen", [])
    log(f"Auswertung geladen: {len(auswertungen)} Dateien")

    log("Erstelle Migrationsplan...")
    plaene, statistik, konflikte = erstelle_migrationsplan(auswertungen)

    schreibe_json(plaene, statistik, konflikte)
    schreibe_csv(plaene, statistik, konflikte)
    schreibe_bericht(plaene, statistik, konflikte)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Gesamtdateien: {len(plaene)}")
    log(f"Konflikte: {len(konflikte)}")
    log(f"Kopierende: {statistik.get('UEBERNEHMEN_KOPIEREND', 0)}")
    for ziel, anzahl in sorted(statistik.items()):
        log(f"  {ziel:<45} {anzahl:>6}")
    log("=" * 60)
    log("CORE-15 MIGRATIONSPLAN ABGESCHLOSSEN")


def selbsttest():
    print("CORE-15 SELBSTTEST =====================================")
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

    t("Ziel-Mapping vollstaendig", len(ZIEL_MAPPING) >= 9)
    t("Projektwurzel existiert", os.path.isdir(PROJEKT_WURZEL))

    # Test berechne_zielpfad
    z = berechne_zielpfad("test.py", "UEBERNEHMEN_KOPIEREND")
    t("Zielpfad enthaelt 02_Kopierte_Dateien", "02_Kopierte_Dateien" in z)

    z2 = berechne_zielpfad("test.py", "DUBLETTE_NICHT_KOPIEREN")
    t("Dublette -> 05_Dubletten", "05_Dubletten" in z2)

    # Test Konflikterkennung
    test_ausw = [
        {"relativer_pfad": "a.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND"},
        {"relativer_pfad": "b.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND"},
    ]
    _, _, k = erstelle_migrationsplan(test_ausw)
    t("Keine Konflikte bei unterschiedlichen Pfaden", len(k) == 0)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
