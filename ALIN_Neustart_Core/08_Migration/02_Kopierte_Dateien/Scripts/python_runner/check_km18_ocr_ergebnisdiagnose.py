#!/usr/bin/env python3
"""KM18 PRUEFDATEI – Validiert KM18-Diagnose-Ausgaben."""
import json, sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "18_OCR_Ergebnisdiagnose"
GESAMT = 0
OK = 0

def pr(kriterium, bedingung, *args):
    global GESAMT, OK
    GESAMT += 1
    if bedingung:
        OK += 1
        print(f"[OK] {GESAMT:5d} - {kriterium}")
    else:
        print(f"[FEHLER] {GESAMT:3d} - {kriterium} " + " ".join(str(a) for a in args))

print("=" * 60)
print("KM18 PRUEFUNG")
print("=" * 60)

# Datei-Existenz
for dname in ["02_Status/KM18_STATUS.json", "03_Berichte/KM18_BERICHT.txt",
              "04_Protokolle/KM18_PROTOKOLL.txt", "05_Fehler/KM18_FEHLER.txt",
              "06_Diagnosen/KM18_DIAGNOSE_DETAIL.json",
              "07_HOCR_Textauszuege/KM18_HOCR_TEXTAUSZUEGE.json",
              "09_Zusammenfassungen/KM18_ZUSAMMENFASSUNG.json",
              "10_Empfehlungen/KM18_EMPFEHLUNGEN.json"]:
    pr(f"Datei {dname}", (SB / dname).exists())

# Status validieren
try:
    status = json.loads((SB / "02_Status/KM18_STATUS.json").read_text(encoding="utf-8"))
    pr("JSON Status gueltig", True)
    pr("Diagnose ausgefuehrt", status.get("diagnose_ausgefuehrt", False))
    pr("OCR nicht wiederholt", status.get("ocr_nicht_wiederholt", True))
    pr("Keine DB-Aenderung", not status.get("datenbank_geaendert", True))
    pr("Keine Original-Aenderung", not status.get("originale_veraendert", True))
    pr("Kein Internet", not status.get("internet_verwendet", True))
    pr("Keine Installation", not status.get("installation_durchgefuehrt", True))
    pr("Keine Produktivfreigabe", not status.get("produktivfreigabe", True))
    pr("Keine Rechtsbewertung", not status.get("rechtsbewertung", True))
    pr("Keine Beweiswuerdigung", not status.get("beweiswuerdigung", True))
except Exception as e:
    pr("Status validieren", False, str(e))

# Zusammenfassung validieren
try:
    zus = json.loads((SB / "09_Zusammenfassungen/KM18_ZUSAMMENFASSUNG.json").read_text(encoding="utf-8"))
    pr("Zusammenfassung JSON gueltig", True)
    pr("Statistik vorhanden", "statistik" in zus)
    pr("HOCR-Zeichen extrahierbar > 0", zus.get("hocr_zeichen_extrahierbar", 0) > 0)
    pr("Ursachenanalyse vorhanden", "ursachenanalyse" in zus)
except Exception as e:
    pr("Zusammenfassung validieren", False, str(e))

# Diagnose-Detail validieren
try:
    diag = json.loads((SB / "06_Diagnosen/KM18_DIAGNOSE_DETAIL.json").read_text(encoding="utf-8"))
    pr("Diagnose-Detail JSON gueltig", True)
    pr("Diagnose-Eintraege > 0", len(diag) > 0)
    for d in diag[:3]:
        pr(f"  TIFF-Check vorhanden ({d.get('original_id','?')[:20]})", "tiff" in d)
        pr(f"  Modi-Check vorhanden", "modi_check" in d)
except Exception as e:
    pr("Diagnose-Detail validieren", False, str(e))

# HOCR-Textauszuege
try:
    hocr = json.loads((SB / "07_HOCR_Textauszuege/KM18_HOCR_TEXTAUSZUEGE.json").read_text(encoding="utf-8"))
    pr("HOCR-Textauszuege JSON gueltig", True)
    if len(hocr) > 0:
        pr("HOCR-Textauszuege > 0", True)
        pr("Erster Auszug enthaelt text_probe", len(hocr[0].get("text_probe", "")) > 0)
except Exception as e:
    pr("HOCR-Textauszuege validieren", False, str(e))

# Empfehlungen
try:
    empf = json.loads((SB / "10_Empfehlungen/KM18_EMPFEHLUNGEN.json").read_text(encoding="utf-8"))
    pr("Empfehlungen JSON gueltig", True)
    kategorien = set(e.get("kategorie","") for e in empf)
    pr("TEXT_SUFFIX-Empfehlung vorhanden", any("SUFFIX" in k for k in kategorien))
    pr("TESSERACT_FLAGS-Empfehlung vorhanden", any("FLAGS" in k or "TESSERACT" in k for k in kategorien))
except Exception as e:
    pr("Empfehlungen validieren", False, str(e))

# Zusammenfassung
print("=" * 60)
if OK == GESAMT:
    print(f"PRUEFUNG: {OK}/{GESAMT} BESTANDEN")
else:
    print(f"PRUEFUNG: {OK}/{GESAMT} BESTANDEN ({GESAMT-OK} FEHLER)")
print("=" * 60)

sys.exit(0 if OK == GESAMT else 1)