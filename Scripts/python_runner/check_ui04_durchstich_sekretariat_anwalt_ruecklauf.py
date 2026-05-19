#!/usr/bin/env python3
"""Pruefdatei fuer UI04 Durchstich Sekretariat -> Anwalt -> Ruecklauf"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI04_Durchstich_Sekretariat_Anwalt_Ruecklauf"

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

print("UI04 PRUEFDATEI =======================================")

# Datei-Existenz
print("\n--- Dateien ---")
t("Status JSON", (SB / "02_Status" / "UI04_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI04_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI04_FEHLER.txt").exists())
t("Manifest JSON", (SB / "07_Manifest" / "UI04_MANIFEST.json").exists())
t("Sekretariat-Vorlage", (SB / "09_Sekretariat_Vorlage" / "UI04_SEKRETARIAT_VORLAGE.json").exists())
t("Anwalt-Freigabe", (SB / "10_Anwalt_Freigabe" / "UI04_ANWALT_FREIGABE_TEMPLATE.json").exists())
t("Ruecklauf", (SB / "11_Ruecklauf_An_Sekretariat" / "UI04_RUECKLAUF_TEMPLATE.json").exists())
t("Sekretariat-Verarbeitung", (SB / "12_Sekretariat_Verarbeitung" / "UI04_SEKRETARIAT_VERARBEITUNG_ERGEBNIS.json").exists())
t("index.html", (SB / "14_Browseransicht" / "index.html").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "14_Browseransicht" / "index.html").exists():
    html = (SB / "14_Browseransicht" / "index.html").read_text(encoding="utf-8")

t("Prozessleiste", "prozessleiste" in html)
t("Dreiansicht", "drei-grid" in html)
t("Dropdown-Rechtsgebiet", "af-rechtsgebiet" in html)
t("Dropdown-Verfahrensland", "af-verfahrensland" in html)
t("Dropdown-Dokumentsprache", "af-dokumentsprache" in html)
t("Dropdown-Dokumentart", "af-dokumentart" in html)
t("Entscheidungsbuttons", "btn-accept" in html and "btn-reject" in html)
t("Notizfelder", "notiz-sekretariat" in html and "notiz-anwalt" in html)
t("JSON-Download", "downloadArbeitsstand" in html)
t("Warnbanner", "warn-banner" in html)
t("Ruecklauf-Anzeige", "ruecklauf-grid" in html)

# JSON-Inhalt
print("\n--- JSON-Inhalt ---")
af = {}
if (SB / "10_Anwalt_Freigabe" / "UI04_ANWALT_FREIGABE_TEMPLATE.json").exists():
    af = json.loads((SB / "10_Anwalt_Freigabe" / "UI04_ANWALT_FREIGABE_TEMPLATE.json").read_text(encoding="utf-8"))
t("Anwalt-Freigabe hat Dropdowns", bool(af.get("dropdowns")))
t("Anwalt-Freigabe hat Entscheidungsoptionen", len(af.get("entscheidungsoptionen", [])) >= 2)

rl = {}
if (SB / "11_Ruecklauf_An_Sekretariat" / "UI04_RUECKLAUF_TEMPLATE.json").exists():
    rl = json.loads((SB / "11_Ruecklauf_An_Sekretariat" / "UI04_RUECKLAUF_TEMPLATE.json").read_text(encoding="utf-8"))
t("Ruecklauf hat Entscheidungsfeld", "anwaltliche_entscheidung" in rl)

sv = {}
if (SB / "12_Sekretariat_Verarbeitung" / "UI04_SEKRETARIAT_VERARBEITUNG_ERGEBNIS.json").exists():
    sv = json.loads((SB / "12_Sekretariat_Verarbeitung" / "UI04_SEKRETARIAT_VERARBEITUNG_ERGEBNIS.json").read_text(encoding="utf-8"))
t("Verarbeitung hat Ergebnisliste", "offene_punkte" in sv or "dokumente_uebernommen" in sv)

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

# Naechster Auftrag
print("\n--- Naechster Auftrag ---")
bericht = ""
if (SB / "03_Berichte" / "UI04_BERICHT.txt").exists():
    bericht = (SB / "03_Berichte" / "UI04_BERICHT.txt").read_text(encoding="utf-8")
t("Naechster Auftrag formuliert", "naechster" in bericht.lower() or "naechste" in bericht.lower() or "folge" in bericht.lower() or len(bericht) > 200)

print(f"\nBESTANDEN: {ok}/{ges}")
if FEHLER:
    print("FEHLER:")
    for f in FEHLER:
        print(f"  - {f}")

sys.exit(0 if ok == ges else 1)
