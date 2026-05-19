#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KM19 Check-Script – prueft Korrektheit der korrigierten Manifeste
"""
import json
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
AG = ROOT / "Agentensteuerung"
KM13_MANIFEST = AG / "13_OCR_Pipeline" / "07_Manifest" / "KM13_OCR_MANIFEST.json"
KM17_MANIFEST = AG / "17_Sprachrouting_OCR" / "07_Manifest" / "KM17_OCR_MANIFEST.json"
KM13_STATUS = AG / "13_OCR_Pipeline" / "02_Status" / "KM13_STATUS.json"
KM17_STATUS = AG / "17_Sprachrouting_OCR" / "02_Status" / "KM17_STATUS.json"
KM19_STATUS = AG / "19_OCR_Betreuer_Korrektur" / "02_Status" / "KM19_STATUS.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    errors = 0
    print("KM19 CHECK")

    km13 = load_json(KM13_MANIFEST)
    km13_ok = sum(1 for e in km13["ergebnisse"] if e.get("ocr_status") == "OK")
    km13_fe = sum(1 for e in km13["ergebnisse"] if e.get("ocr_status") == "FEHLER")
    print(f"  KM13 Manifest: {km13_ok} OK, {km13_fe} FEHLER (erwartet 24 OK, 0 FEHLER)")
    if km13_ok != 24 or km13_fe != 0:
        print("  FEHLER: KM13 nicht 24/24")
        errors += 1

    km17 = load_json(KM17_MANIFEST)
    # KM17 uses flat structure with ocr_statistik
    if "ergebnisse" in km17:
        km17_ok = sum(1 for e in km17["ergebnisse"] if e.get("ocr_status") == "OK")
        km17_fe = sum(1 for e in km17["ergebnisse"] if e.get("ocr_status") == "FEHLER")
    else:
        km17_ok = km17.get("ocr_statistik", {}).get("OK", 0)
        km17_fe = km17.get("ocr_statistik", {}).get("FEHLER", 0)
    print(f"  KM17 Manifest: {km17_ok} OK, {km17_fe} FEHLER (erwartet 24 OK, 0 FEHLER)")
    if km17_ok != 24 or km17_fe != 0:
        print("  FEHLER: KM17 nicht 24/24")
        errors += 1

    s13 = load_json(KM13_STATUS)
    print(f"  KM13 Status ocr_erfolgreich: {s13.get('ocr_erfolgreich', '?')}")
    s17 = load_json(KM17_STATUS)
    print(f"  KM17 Status OK: {s17.get('ocr_statistik', {}).get('OK', '?')}")

    if KM19_STATUS.exists():
        s19 = load_json(KM19_STATUS)
        print(f"  KM19 Status: phase2_erfolge={s19.get('phase2_erfolge', '?')}")

    if errors:
        print(f"RESULT: {errors} FEHLER")
        return 1
    print("RESULT: ALL OK")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
