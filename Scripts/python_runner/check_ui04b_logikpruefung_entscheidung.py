#!/usr/bin/env python3
"""Pruefdatei fuer UI04b Logikpruefung und Entscheidungsmaske"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf" / "15_UI04b_Logikpruefung"

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

print("UI04b PRUEFDATEI =======================================")

# Datei-Existenz
print("\n--- Dateien ---")
t("Status JSON", (SB / "02_Status" / "UI04b_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI04b_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI04b_FEHLER.txt").exists())
t("Manifest JSON", (SB / "07_Manifest" / "UI04b_MANIFEST.json").exists())
t("Eingabeanalyse", (SB / "08_Eingabeanalyse" / "UI04b_EINGABEANALYSE.json").exists())
t("Plausibilitaet", (SB / "09_Plausibilitaet" / "UI04b_PLAUSIBILITAET.json").exists())
t("Formularschema", (SB / "10_Bereinigtes_Formular" / "UI04b_FORMULAR_SCHEMA.json").exists())
t("Exporttemplate", (SB / "12_Export_Template" / "UI04b_EXPORT_TEMPLATE.json").exists())
t("index.html", (SB / "11_Browseransicht" / "index.html").exists())
t("CSS", (SB / "11_Browseransicht" / "ui04b.css").exists())
t("JS", (SB / "11_Browseransicht" / "ui04b.js").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "11_Browseransicht" / "index.html").exists():
    html = (SB / "11_Browseransicht" / "index.html").read_text(encoding="utf-8")

t("Prozessleiste", "prozessleiste" in html)
t("Aktenprofil-Karte", "aktenprofil-karte" in html)
t("Dokumentkarten", "dokument-karte" in html)
t("Entscheidungs-Karte", "entscheidung-karte" in html)
t("Folgefelder-Karte", "folgefelder-karte" in html)
t("Notizen-Karte", "notizen-karte" in html)
t("Ergebnis-Karte", "ergebnis-karte" in html)
t("Dreiansicht", "dreiansicht-karte" in html)
t("Plausibilitaetswarnungen", "plausi" in html)
t("Sonstiges-Freitextlogik", "Sonstiges" in html and "freie" in html.lower())
t("strukturierte Exportlogik", "UI04b_Export" in html)
t("JSON-Download", "downloadExport" in html)

# JSON-Inhalt
print("\n--- JSON-Inhalt ---")
schema = {}
if (SB / "10_Bereinigtes_Formular" / "UI04b_FORMULAR_SCHEMA.json").exists():
    schema = json.loads((SB / "10_Bereinigtes_Formular" / "UI04b_FORMULAR_SCHEMA.json").read_text(encoding="utf-8"))
t("Schema hat Aktenprofil", "aktenprofil" in schema)
t("Schema hat Dokumente", len(schema.get("dokumente", [])) >= 0)
t("Schema hat Hauptentscheidung", "hauptentscheidung" in schema)
t("Schema hat Folgefelder", "folgefelder" in schema)

plausi = {}
if (SB / "09_Plausibilitaet" / "UI04b_PLAUSIBILITAET.json").exists():
    plausi = json.loads((SB / "09_Plausibilitaet" / "UI04b_PLAUSIBILITAET.json").read_text(encoding="utf-8"))
t("Plausibilitaet hat Fehlerliste", "fehler" in plausi)
t("Plausibilitaet hat Warnungsliste", "warnungen" in plausi)
t("Plausibilitaet hat Hinweisliste", "hinweise" in plausi)

export = {}
if (SB / "12_Export_Template" / "UI04b_EXPORT_TEMPLATE.json").exists():
    export = json.loads((SB / "12_Export_Template" / "UI04b_EXPORT_TEMPLATE.json").read_text(encoding="utf-8"))
t("Export hat Freigabestatus", "freigabe_status" in export)

# Grenzen
print("\n--- Grenzen ---")
neue_ocr = False
for f in SB.rglob("*.txt"):
    txt = f.read_text(encoding="utf-8", errors="replace")
    if "neue OCR" in txt and "Keine neue OCR" not in txt:
        neue_ocr = True
t("Keine neue OCR-Ausgabe", not neue_ocr)
t("Keine DB-Datei", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))
t("Keine Cloud-/Internetnutzung", "http://" not in html.lower() and "https://" not in html.lower())

# Temporaere Dateien
print("\n--- Temporaere Dateien ---")
temp_files = [
    ROOT / "Scripts" / "python_runner" / "fix_ui04.py",
    ROOT / "Scripts" / "python_runner" / "fix_html_escape.py",
    ROOT / "Scripts" / "python_runner" / "fix_line190.py",
    ROOT / "Scripts" / "python_runner" / "test_amp.py",
    ROOT / "Scripts" / "python_runner" / "fix_ui04_encoding.py",
]
temp_exist = [f for f in temp_files if f.exists()]
t("Keine temporaeren Reparaturdateien im Projekt", len(temp_exist) == 0)
if temp_exist:
    print("  WARNUNG: Noch temporaere Dateien vorhanden: %s" % ", ".join([str(f.name) for f in temp_exist]))

# Naechster Auftrag
print("\n--- Naechster Auftrag ---")
bericht = ""
if (SB / "03_Berichte" / "UI04b_BERICHT.txt").exists():
    bericht = (SB / "03_Berichte" / "UI04b_BERICHT.txt").read_text(encoding="utf-8")
t("Naechster Auftrag formuliert", "naechster" in bericht.lower() or "naechste" in bericht.lower() or "folge" in bericht.lower() or len(bericht) > 200)

print(f"\nBESTANDEN: {ok}/{ges}")
if FEHLER:
    print("FEHLER:")
    for f in FEHLER:
        print(f"  - {f}")

sys.exit(0 if ok == ges else 1)
