# -*- coding: utf-8 -*-
"""KM19 OCR-Gesamtkette Pruefdatei – check_km19_ocr_gesamtkette_synchronisieren"""
import sys, json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
BEREICH = ROOT / "Agentensteuerung" / "19_OCR_Gesamtkette_Synchronisieren"

def pruefe():
    tests_ok = 0
    tests_gesamt = 0
    def t(bez, bed):
        nonlocal tests_ok, tests_gesamt
        tests_gesamt += 1
        if bed:
            tests_ok += 1
            print(f"  [OK] {bez}")
        else:
            print(f"  [FEHLER] {bez}")

    print("=" * 50)
    print("KM19 PRUEFDATEI")
    print("=" * 50)

    t("1  Status vorhanden", (BEREICH / "02_Status" / "KM19_STATUS.json").exists())
    t("2  Manifest vorhanden", (BEREICH / "07_Manifest" / "KM19_MANIFEST.json").exists())
    t("3  Manifest CSV vorhanden", (BEREICH / "07_Manifest" / "KM19_MANIFEST.csv").exists())
    t("4  Bericht vorhanden", (BEREICH / "03_Berichte" / "KM19_BERICHT.txt").exists())
    t("5  Fehlerbericht vorhanden", (BEREICH / "05_Fehler" / "KM19_FEHLER.txt").exists())
    t("6  Vergleich vorhanden", (BEREICH / "09_Vergleich" / "KM19_VERGLEICH_VORHER_NACHHER.json").exists())
    t("7  Vergleich CSV vorhanden", (BEREICH / "09_Vergleich" / "KM19_VERGLEICH_VORHER_NACHHER.csv").exists())
    t("8  Rueckbindung vorhanden", (BEREICH / "10_Rueckbindung" / "KM19_RUECKBINDUNG.json").exists())
    t("9  Ausfuehrungsnotiz vorhanden", (BEREICH / "13_Ausfuehrungsnotizen" / "KM19_AUSFUEHRUNGSNOTIZ.txt").exists())
    t("10 Synchro-JSON vorhanden", (BEREICH / "08_Synchronisierte_OCR" / "KM19_SYNCHRONISIERTE_OCR.json").exists())
    t("11 Synchro-CSV vorhanden", (BEREICH / "08_Synchronisierte_OCR" / "KM19_SYNCHRONISIERTE_OCR.csv").exists())

    # Inhaltspruefungen
    if (BEREICH / "02_Status" / "KM19_STATUS.json").exists():
        status = json.loads((BEREICH / "02_Status" / "KM19_STATUS.json").read_text(encoding="utf-8"))
        t("12 KM17c OK", status.get("km17c_ok") == True)
        t("13 Original unveraendert", status.get("originale_veraendert") == False)
        t("14 Keine DB-Aenderung", status.get("datenbank_aenderungen") == False)
        t("15 Keine Internetnutzung", status.get("internet_verwendet") == False)
        t("16 Keine Produktivfreigabe", status.get("produktivfreigabe") == False)
        t("17 Fehlerzahl 0", status.get("fehler_anzahl", -1) == 0)

    if (BEREICH / "07_Manifest" / "KM19_MANIFEST.json").exists():
        manifest = json.loads((BEREICH / "07_Manifest" / "KM19_MANIFEST.json").read_text(encoding="utf-8"))
        t("18 Manifest OCR OK", manifest.get("km13_nachher_ok", 0) == 24)
        t("19 Manifest OCR FEHLER 0", manifest.get("km13_nachher_fehler", -1) == 0)
        t("20 Dateien sync >0", len(manifest.get("dateien_synchronisiert", [])) > 0)

    if (BEREICH / "10_Rueckbindung" / "KM19_RUECKBINDUNG.json").exists():
        rb = json.loads((BEREICH / "10_Rueckbindung" / "KM19_RUECKBINDUNG.json").read_text(encoding="utf-8"))
        t("21 Rueckbindungskette 7", len(rb.get("kette", [])) == 7)
        t("22 Zielseite korrekt", rb.get("zielseite", {}).get("original_id") == "ORG-9dd16304b3b5-00162")

    print("")
    print(f"PRUEFUNG: {tests_ok}/{tests_gesamt} BESTANDEN")
    return tests_ok == tests_gesamt

if __name__ == "__main__":
    ok = pruefe()
    sys.exit(0 if ok else 1)
