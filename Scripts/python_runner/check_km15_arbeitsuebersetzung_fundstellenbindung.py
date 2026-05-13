# -*- coding: utf-8 -*-
"""
CHECK KM15 – ARBEITSUEBERSETZUNGSSCHICHT MIT FUNDSTELLENBINDUNG
===============================================================

Prueft saemtliche KM15-Ausgaben auf Korrektheit und Grenzeinhaltung.
"""

import sys
import json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "15_Arbeitsuebersetzung_Fundstellenbindung"

STATUS_FILE = SB / "02_Status" / "KM15_STATUS.json"
MANIFEST_JSON = SB / "07_Manifest" / "KM15_MANIFEST.json"
MANIFEST_CSV = SB / "07_Manifest" / "KM15_MANIFEST.csv"
BERICHT = SB / "03_Berichte" / "KM15_BERICHT.txt"
FEHLERBERICHT = SB / "05_Fehler" / "KM15_FEHLER.txt"
AUSFUEHRUNGSNOTIZ = SB / "13_Ausfuehrungsnotizen" / "KM15_AUSFUEHRUNGSNOTIZ.txt"
UE_DIR = SB / "08_Uebersetzungseinheiten"
US_JSON = SB / "09_Unsicherheiten" / "KM15_UNSICHERHEITEN.json"
US_CSV = SB / "09_Unsicherheiten" / "KM15_UNSICHERHEITEN.csv"
CONFIG_FILE = ROOT / "Config" / "arbeitsuebersetzung_fundstellenbindung_v1.json"

PLATZHALTER_STATUS = "uebersetzung_nicht_ausgefuehrt_lokales_modell_nicht_angebunden"


def check(cond, num, desc):
    if cond:
        print(f"[OK] {num:3d} – {desc}")
        return True
    else:
        print(f"[FEHLER] {num:3d} – {desc}")
        return False


def main():
    print("=" * 60)
    print("KM15 PRUEFUNG – ARBEITSUEBERSETZUNGSSCHICHT")
    print("=" * 60)

    bestanden = 0
    num = 0

    # 1-6: Ausgabedateien vorhanden
    ausgaben = [
        (STATUS_FILE, "Status JSON"),
        (MANIFEST_JSON, "Manifest JSON"),
        (MANIFEST_CSV, "Manifest CSV"),
        (BERICHT, "Bericht"),
        (FEHLERBERICHT, "Fehlerbericht"),
        (AUSFUEHRUNGSNOTIZ, "Ausfuehrungsnotiz"),
        (US_JSON, "Unsicherheiten JSON"),
        (US_CSV, "Unsicherheiten CSV"),
        (CONFIG_FILE, "Konfigurationsdatei"),
    ]
    for pfad, name in ausgaben:
        num += 1
        bestanden += check(pfad.exists(), num, f"{name} vorhanden")

    # 10: Status Pflichtfelder
    if STATUS_FILE.exists():
        s = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        pflicht = [
            "modul", "version", "zeitpunkt", "uebersetzungsstatus",
            "lokales_modell_verfuegbar", "uebersetzung_aktiv",
            "grenze_uebersetzung", "grenze_rechtsbewertung",
            "grenze_originalaenderung", "grenze_db_aenderung",
            "produktivfreigabe",
        ]
        num += 1
        bestanden += check(all(k in s for k in pflicht), num, "Status Pflichtfelder vollstaendig")

        # 11: Uebersetzungsstatus = Platzhalter
        num += 1
        bestanden += check(
            s.get("uebersetzungsstatus") == PLATZHALTER_STATUS,
            num, "Uebersetzungsstatus = Platzhalter"
        )

        # 12: Kein Modell
        num += 1
        bestanden += check(
            s.get("lokales_modell_verfuegbar") == False,
            num, "Lokales Modell NICHT verfuegbar (korrekt)"
        )

        # 13: Keine Uebersetzung aktiv
        num += 1
        bestanden += check(
            s.get("uebersetzung_aktiv") == False,
            num, "Uebersetzung NICHT aktiv (korrekt)"
        )

        # 14-19: Grenzen
        grenzen = [
            ("grenze_uebersetzung", "Keine endgueltige Uebersetzung"),
            ("grenze_rechtsbewertung", "Keine Rechtsbewertung"),
            ("grenze_originalaenderung", "Keine Originalaenderung"),
            ("grenze_db_aenderung", "Keine DB-Aenderung"),
            ("grenze_internet", "Kein Internet"),
            ("grenze_cloud", "Keine Cloud"),
        ]
        for k, desc in grenzen:
            num += 1
            bestanden += check(s.get(k, False) == True, num, desc)

        # 20: Produktivfreigabe false
        num += 1
        bestanden += check(s.get("produktivfreigabe") == False, num, "Keine Produktivfreigabe")

    # 21: Manifest enthaelt Uebersetzungseinheiten-Infos
    if MANIFEST_JSON.exists():
        m = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        num += 1
        bestanden += check("uebersetzungseinheiten_dateien" in m, num, "Manifest: Uebersetzungseinheiten-Dateien")
        num += 1
        bestanden += check(m.get("uebersetzungsstatus") == PLATZHALTER_STATUS, num, "Manifest: Platzhalter-Status")

    # 22: Uebersetzungseinheiten-Verzeichnis existiert
    num += 1
    bestanden += check(UE_DIR.exists(), num, "Uebersetzungseinheiten-Verzeichnis vorhanden")

    # 23: Uebersetzungseinheiten-Dateien haben korrekte Struktur
    ue_files = list(UE_DIR.glob("*_uebersetzungseinheiten.json"))
    if ue_files:
        ue_ok = True
        for uf in ue_files:
            try:
                d = json.loads(uf.read_text(encoding="utf-8"))
                if not all(k in d for k in ["original_id", "uebersetzungseinheiten", "uebersetzungsstatus"]):
                    ue_ok = False
            except Exception:
                ue_ok = False
        num += 1
        bestanden += check(ue_ok, num, f"Uebersetzungseinheiten-Dateien korrekt ({len(ue_files)} Dateien)")

    # 24: Keine Uebersetzungstexte erzeugt (nur Platzhalter)
    if ue_files:
        hat_uebersetzung = False
        for uf in ue_files:
            try:
                d = json.loads(uf.read_text(encoding="utf-8"))
                for ue in d.get("uebersetzungseinheiten", []):
                    if ue.get("uebersetzung_text") is not None:
                        hat_uebersetzung = True
                        break
            except Exception:
                pass
        num += 1
        bestanden += check(not hat_uebersetzung, num, "Keine erfundenen Uebersetzungen")

    # 25: JSON-Dateien gueltig
    json_files = [f for f in [STATUS_FILE, MANIFEST_JSON, US_JSON] if f.exists()]
    all_valid = True
    for jf in json_files:
        try:
            json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            all_valid = False
    num += 1
    bestanden += check(all_valid, num, "Alle JSON-Dateien gueltig")

    print()
    print("=" * 60)
    print(f"PRUEFUNG: {bestanden}/{num} BESTANDEN")
    print("=" * 60)
    return bestanden == num


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
