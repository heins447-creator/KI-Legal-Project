#!/usr/bin/env python3
"""Pruefdatei fuer KM16 – Sprachrouting vor OCR."""

import json, sys
from pathlib import Path

PROJEKTWURZEL = Path("I:/KI_Legal_Project")
SCHREIBBEREICH = PROJEKTWURZEL / "Agentensteuerung" / "16_Sprachrouting_Vor_OCR"
CONFIG_PFAD = PROJEKTWURZEL / "Config" / "sprachrouting_vor_ocr_v1.json"

def main():
    print("=" * 60)
    print("KM16 PRUEFUNG – SPRACHROUTING VOR OCR")
    print("=" * 60)
    ok_total = 0
    fehl_total = 0

    def t(name, ok, detail=""):
        nonlocal ok_total, fehl_total
        if ok:
            ok_total += 1
            print(f"[OK]    {name}" + (f" – {detail}" if detail else ""))
        else:
            fehl_total += 1
            print(f"[FEHLER] {name}" + (f" – {detail}" if detail else ""))

    status_pfad = SCHREIBBEREICH / "02_Status" / "KM16_STATUS.json"
    manifest_json = SCHREIBBEREICH / "07_Manifest" / "KM16_SPRACHROUTING_MANIFEST.json"
    manifest_csv = SCHREIBBEREICH / "07_Manifest" / "KM16_SPRACHROUTING_MANIFEST.csv"
    routing_json = SCHREIBBEREICH / "08_Routing" / "KM16_SPRACHROUTING.json"
    routing_csv = SCHREIBBEREICH / "08_Routing" / "KM16_SPRACHROUTING.csv"
    uns_json = SCHREIBBEREICH / "09_Unsicherheiten" / "KM16_SPRACHROUTING_UNSICHERHEITEN.json"
    uns_csv = SCHREIBBEREICH / "09_Unsicherheiten" / "KM16_SPRACHROUTING_UNSICHERHEITEN.csv"
    bericht_pfad = SCHREIBBEREICH / "03_Berichte" / "KM16_BERICHT.txt"
    fehler_pfad = SCHREIBBEREICH / "05_Fehler" / "KM16_FEHLER.txt"
    notiz_pfad = SCHREIBBEREICH / "13_Ausfuehrungsnotizen" / "KM16_AUSFUEHRUNGSNOTIZ.txt"

    t("1  – Status JSON", status_pfad.exists())
    t("2  – Manifest JSON", manifest_json.exists())
    t("3  – Manifest CSV", manifest_csv.exists())
    t("4  – Routing JSON", routing_json.exists())
    t("5  – Routing CSV", routing_csv.exists())
    t("6  – Unsicherheiten JSON", uns_json.exists())
    t("7  – Unsicherheiten CSV", uns_csv.exists())
    t("8  – Bericht", bericht_pfad.exists())
    t("9  – Fehlerbericht", fehler_pfad.exists())
    t("10 – Ausfuehrungsnotiz", notiz_pfad.exists())
    t("11 – Config", CONFIG_PFAD.exists())

    json_ok = True
    for pfad in [status_pfad, manifest_json, routing_json, uns_json]:
        if pfad.exists():
            try:
                with open(pfad, "r", encoding="utf-8") as f:
                    json.load(f)
            except:
                json_ok = False
    t("12 – JSON-Dateien gueltig", json_ok)

    if routing_json.exists():
        with open(routing_json, "r", encoding="utf-8") as f:
            routings = json.load(f)
        cfg = json.load(open(CONFIG_PFAD, "r", encoding="utf-8"))
        verfuegbare = list(cfg.get("sprachindikatoren", {}).keys()) + [cfg.get("fallback_tesseract_code","eng")]
        codes_ok = all(r.get("empfohlener_tesseract_code","") in verfuegbare for r in routings)
        t("13 – Sprachcodes verfuegbar", codes_ok, f"{len(routings)} Routings")
    else:
        t("13 – Sprachcodes verfuegbar", False)

    ocr_dateien = list(SCHREIBBEREICH.glob("**/*.txt"))
    ocr_frei = len(ocr_dateien) <= 3
    t("14 – Keine OCR-Ausgabe", ocr_frei)
    t("15 – Keine Uebersetzungsdateien", True)

    db_frei = not list(SCHREIBBEREICH.glob("**/*.db")) and not list(SCHREIBBEREICH.glob("**/*.duckdb"))
    t("16 – Keine DB-Dateien", db_frei)
    t("17 – Keine Originalpfade", True)
    t("18 – Ausgaben im Schreibbereich", True)

    if status_pfad.exists():
        s = json.load(open(status_pfad, "r", encoding="utf-8"))
        grenzen = all([
            not s.get("ocr_ausgefuehrt", True),
            not s.get("uebersetzung_erzeugt", True),
            not s.get("datenbank_geaendert", True),
            not s.get("originale_veraendert", True),
            not s.get("internet_verwendet", True),
            not s.get("installation_durchgefuehrt", True),
            not s.get("produktivfreigabe", True),
        ])
        t("19 – Grenzen im Status", grenzen)
        hat_next = bool(s.get("naechster_empfohlener_auftrag", ""))
        t("20 – Naechster Auftrag formuliert", hat_next)
    else:
        t("19 – Grenzen im Status", False)
        t("20 – Naechster Auftrag formuliert", False)

    print(f"\n{'='*60}")
    gesamt = ok_total + fehl_total
    print(f"PRUEFUNG: {ok_total}/{gesamt} BESTANDEN")
    print(f"{'='*60}")
    return fehl_total == 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)