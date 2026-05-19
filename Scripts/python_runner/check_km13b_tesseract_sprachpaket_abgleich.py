# -*- coding: utf-8 -*-
"""
CHECK KM13b – TESSERACT-SPRACHPAKET-ABGLEICH (PRUEFDATEI)
===========================================================

Prueft saemtliche KM13b-Ausgaben auf Korrektheit und Grenzeinhaltung.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "13b_Tesseract_Sprachpaket_Abgleich"

STATUS_FILE = SB / "02_Status" / "KM13b_STATUS.json"
MANIFEST_JSON = SB / "07_Manifest" / "KM13b_MANIFEST.json"
MANIFEST_CSV = SB / "07_Manifest" / "KM13b_MANIFEST.csv"
BERICHT = SB / "03_Berichte" / "KM13b_BERICHT.txt"
FEHLERBERICHT = SB / "05_Fehler" / "KM13b_FEHLER.txt"
AUSFUEHRUNGSNOTIZ = SB / "13_Ausfuehrungsnotizen" / "KM13b_AUSFUEHRUNGSNOTIZ.txt"
CONFIG_FILE = ROOT / "Config" / "tesseract_sprachpaket_abgleich_v1.json"

EU24_CODES = {
    "bul", "hrv", "ces", "dan", "nld", "eng", "est", "fin", "fra",
    "deu", "ell", "hun", "gle", "ita", "lav", "lit", "mlt", "pol",
    "por", "ron", "slk", "slv", "spa", "swe",
}


def check(cond, num, desc):
    if cond:
        print(f"[OK] {num:3d} – {desc}")
        return True
    else:
        print(f"[FEHLER] {num:3d} – {desc}")
        return False


def main():
    print("=" * 60)
    print("KM13b PRUEFUNG – TESSERACT-SPRACHPAKET-ABGLEICH")
    print("=" * 60)

    bestanden = 0
    num = 0

    # 1: Statusdatei
    num += 1
    bestanden += check(STATUS_FILE.exists(), num, "Status JSON vorhanden")

    # 2: Manifest JSON
    num += 1
    bestanden += check(MANIFEST_JSON.exists(), num, "Manifest JSON vorhanden")

    # 3: Manifest CSV
    num += 1
    bestanden += check(MANIFEST_CSV.exists(), num, "Manifest CSV vorhanden")

    # 4: Bericht
    num += 1
    bestanden += check(BERICHT.exists(), num, "Bericht vorhanden")

    # 5: Fehlerbericht
    num += 1
    bestanden += check(FEHLERBERICHT.exists(), num, "Fehlerbericht vorhanden")

    # 6: Ausfuehrungsnotiz
    num += 1
    bestanden += check(AUSFUEHRUNGSNOTIZ.exists(), num, "Ausfuehrungsnotiz vorhanden")

    # 7: Config vorhanden
    num += 1
    bestanden += check(CONFIG_FILE.exists(), num, "Konfigurationsdatei vorhanden")

    # 8: Status enthaelt Pflichtfelder
    if STATUS_FILE.exists():
        s = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        status_checks = all(k in s for k in [
            "modul", "version", "zeitpunkt", "anzahl_exe_pfade",
            "anzahl_tessdata_pfade", "sprachen_gesamt",
            "eu24_vorhanden", "eu24_fehlen",
            "installation_durchgefuehrt", "internet_verwendet",
            "originale_veraendert", "datenbank_geaendert"
        ])
        num += 1
        bestanden += check(status_checks, num, "Status pflichtfelder vollstaendig")

        # 9: Keine Installation
        num += 1
        bestanden += check(
            s.get("installation_durchgefuehrt") == False,
            num, "Keine Installation von Sprachpaketen"
        )

        # 10: Kein Internet
        num += 1
        bestanden += check(
            s.get("internet_verwendet") == False,
            num, "Kein Internet verwendet"
        )

        # 11: Keine Originalaenderung
        num += 1
        bestanden += check(
            s.get("originale_veraendert") == False,
            num, "Keine Originale veraendert"
        )

        # 12: Keine DB-Aenderung
        num += 1
        bestanden += check(
            s.get("datenbank_geaendert") == False,
            num, "Keine Datenbankaenderung"
        )

    # 13: Manifest enthaelt EU24-Abgleich
    if MANIFEST_JSON.exists():
        m = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        has_eu = "eu24_status" in m
        num += 1
        bestanden += check(has_eu, num, "Manifest enthaelt EU24-Status")

        if has_eu:
            eu_keys = set(m["eu24_status"].keys())
            num += 1
            bestanden += check(
                eu_keys == EU24_CODES,
                num, f"Manifest EU24-Schluessel vollstaendig ({len(eu_keys)})"
            )

    # 14: EXE-Pfade gefunden
    if STATUS_FILE.exists():
        num += 1
        bestanden += check(
            s.get("anzahl_exe_pfade", 0) >= 1,
            num, "Mindestens 1 Tesseract-EXE gefunden"
        )

    # 15: Tessdata-Pfade gefunden
    if STATUS_FILE.exists():
        num += 1
        bestanden += check(
            s.get("anzahl_tessdata_pfade", 0) >= 1,
            num, "Mindestens 1 Tessdata-Verzeichnis gefunden"
        )

    # 16: Sprachen gefunden
    if STATUS_FILE.exists():
        num += 1
        bestanden += check(
            s.get("sprachen_gesamt", 0) >= 1,
            num, "Mindestens 1 Sprache gefunden"
        )

    # 17: Bericht kein leeres File
    if BERICHT.exists():
        content = BERICHT.read_text(encoding="utf-8")
        num += 1
        bestanden += check(len(content) > 200, num, "Bericht enthaelt Inhalt")

    # 18: Manifest CSV
    if MANIFEST_CSV.exists():
        csvc = MANIFEST_CSV.read_text(encoding="utf-8")
        num += 1
        bestanden += check("sprachcode" in csvc and "eu24_status" in csvc,
                          num, "Manifest CSV Header korrekt")

    # 19: Alle Ausgaben im Schreibbereich
    ausgaben = [STATUS_FILE, MANIFEST_JSON, MANIFEST_CSV, BERICHT, FEHLERBERICHT, AUSFUEHRUNGSNOTIZ]
    alle_im_sb = all(str(SB) in str(a) for a in ausgaben if a.exists())
    num += 1
    bestanden += check(alle_im_sb, num, "Alle Ausgaben im Schreibbereich")

    # 20: JSON-Dateien gueltig
    json_files = [f for f in [STATUS_FILE, MANIFEST_JSON] if f.exists()]
    all_json_valid = True
    for jf in json_files:
        try:
            json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            all_json_valid = False
    num += 1
    bestanden += check(all_json_valid, num, "Alle JSON-Dateien gueltig")

    print()
    print("=" * 60)
    print(f"PRUEFUNG: {bestanden}/{num} BESTANDEN")
    print("=" * 60)
    return bestanden == num


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
