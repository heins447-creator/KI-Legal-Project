#!/usr/bin/env python3
"""Prüfdatei für UI03-1 Anwalts-Dreiansicht"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "20_Anwalts_Dreiansicht"

FEHLER = []
WARNUNGEN = []
ok = 0
ges = 0

def t(bez, bed):
    global ok, ges
    ges += 1
    v = bool(bed)
    print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
    if not v:
        FEHLER.append(bez)
    else:
        ok += 1

print("UI03-1 PRÜFDATEI =======================================")

# Datei-Existenz
print("\n--- Dateien ---")
t("Status JSON", (SB / "02_Status" / "UI03_1_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI03_1_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI03_1_FEHLER.txt").exists())
t("Manifest JSON", (SB / "07_Manifest" / "UI03_1_MANIFEST.json").exists())
t("ViewData", (SB / "08_ViewData" / "UI03_1_VIEWDATA.json").exists())
t("OCR-Text JSON", (SB / "09_OCR_Text" / "UI03_1_OCR_TEXT.json").exists())
t("Deutsche Arbeitsansicht JSON", (SB / "10_Deutsche_Arbeitsansicht" / "UI03_1_DEUTSCHE_ARBEITSANSICHT.json").exists())
t("Zuordnungstemplate", (SB / "11_Zuordnung" / "UI03_1_ZUORDNUNG_TEMPLATE.json").exists())
t("Agentenauftrag-Template", (SB / "12_Agentenauftraege" / "UI03_1_AGENTENAUFTRAG_TEMPLATE.json").exists())
t("Notiztemplate", (SB / "13_Notizen" / "UI03_1_NOTIZ_TEMPLATE.json").exists())
t("index.html", (SB / "14_Browseransicht" / "index.html").exists())
t("CSS", (SB / "14_Browseransicht" / "ui03_1.css").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "14_Browseransicht" / "index.html").exists():
    html = (SB / "14_Browseransicht" / "index.html").read_text(encoding="utf-8")

t("Original-Spalte", "original-spalte" in html)
t("OCR-Spalte", "ocr-spalte" in html)
t("Deutsche Arbeitsansicht", "de-spalte" in html)
t("Mehrfachauswahl", "dok-select" in html and "checkbox" in html)
t("Dokumentart-Dropdown", "dokart-" in html)
t("Dokumentart-Sonstiges-Freitext", "dokart-sonst-" in html)
t("Rechtsgebiet-Dropdown", "rg-rechtsgebiet" in html)
t("Rechtsgebiet-Sonstiges-Freitext", "rg-rechtsgebiet-sonst" in html)
t("Arbeitsrecht-Streitpunkte", "Arbeitsrecht" in html)
t("Streitpunkt-Sonstiges-Freitext", "sonstiges-freitext" in html)
t("Sachverhaltszuordnung", "sachverhalt-checkboxes" in html)
t("Sachverhalt-Sonstiges-Freitext", "Sonstiges" in html)
t("Agentenaufträge", "agenten-chips" in html)
t("Agentenauftrag-Sonstiges-Freitext", "agenten-sonstiges" in html)
t("Notizfelder", "notiz-anwalt" in html)
t("Suche", "suchfeld" in html)
t("JSON-Download", "Blob" in html and "application/json" in html)

# ViewData
print("\n--- ViewData ---")
vd = {}
if (SB / "08_ViewData" / "UI03_1_VIEWDATA.json").exists():
    vd = json.loads((SB / "08_ViewData" / "UI03_1_VIEWDATA.json").read_text(encoding="utf-8"))
t("ViewData hat Akten-ID", bool(vd.get("akten_id")))
t("ViewData hat Dokumente", len(vd.get("dokumente", [])) >= 1)
t("ViewData hat Dropdowns", bool(vd.get("dropdowns")))

# Grenzen
print("\n--- Grenzen ---")
neue_ocr = False
for f in SB.rglob("*.txt"):
    if "neue OCR" in f.read_text(encoding="utf-8", errors="replace"):
        neue_ocr = True
t("Keine neue OCR-Ausgabe", not neue_ocr)
t("Keine DB-Datei", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))
t("Keine Cloud-/Internetnutzung", "http://" not in html.lower() and "https://" not in html.lower())

# Nächster Auftrag
print("\n--- Nächster Auftrag ---")
bericht = ""
if (SB / "03_Berichte" / "UI03_1_BERICHT.txt").exists():
    bericht = (SB / "03_Berichte" / "UI03_1_BERICHT.txt").read_text(encoding="utf-8")
t("Nächster Auftrag formuliert", "noch nicht vorhanden" in bericht.lower() or "naechster" in bericht.lower())

print(f"\nBESTANDEN: {ok}/{ges}")
if FEHLER:
    print("FEHLER:")
    for f in FEHLER:
        print(f"  - {f}")

sys.exit(0 if ok == ges else 1)
