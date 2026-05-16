#!/usr/bin/env python3
"""Prüfdatei für UI03-1d OCR-Freigabeablauf (CORE-11-konform)."""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "23_OCR_Freigabeablauf_UI03_1d"

FEHLER = []
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

print("UI03-1d OCR-FREIGABEABLAUF PRÜFDATEI ================================")

# Register-Existenz
print("\n--- CORE-11 Register ---")
t("Toolregister vorhanden", (CORE / "toolregister.json").exists())
t("Ressourcenregister vorhanden", (CORE / "ressourcenregister.json").exists())
t("Schnittstellenregister vorhanden", (CORE / "schnittstellenregister.json").exists())
t("Modulregister vorhanden", (CORE / "modulregister.json").exists())

# Register-Inhalt
print("\n--- Register-Inhalt ---")
if (CORE / "toolregister.json").exists():
    tr = json.loads((CORE / "toolregister.json").read_text(encoding="utf-8-sig"))
    tools = [t.get("tool_id") for t in tr.get("eintraege", []) if t.get("tool_id")]
    t("Tesseract im Toolregister", "TESSERACT" in tools)

# Ausgaben
print("\n--- Ausgaben ---")
t("Freigabe-HTML", (SB / "02_Status" / "UI03_1d_OCR_FREIGABEABLAUF.html").exists())
t("Status-JSON", (SB / "02_Status" / "UI03_1d_OCR_FREIGABEABLAUF.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI03_1d_OCR_FREIGABEABLAUF_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI03_1d_OCR_FREIGABEABLAUF_FEHLER.txt").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "02_Status" / "UI03_1d_OCR_FREIGABEABLAUF.html").exists():
    html = (SB / "02_Status" / "UI03_1d_OCR_FREIGABEABLAUF.html").read_text(encoding="utf-8")

t("HTML enthält Seiten-Karten", "seiten-karte" in html)
t("HTML enthält Radio-Buttons", 'type="radio"' in html)
t("HTML enthält 4 Freigabe-Optionen", html.count('type="radio"') >= 4)
t("HTML enthält Anmerkungs-Freitext", "freitext-seite" in html)
t("HTML enthält OCR-Vorschau", "OCR-Text" in html)
t("HTML enthält Orientierungsübersetzung", "Orientierungsübersetzung" in html)
t("HTML enthält Gesamtübersicht", "gesamt-panel" in html)
t("HTML enthält Dokument-Metadaten", "Dokument:" in html)
t("HTML enthält Seiten-Status", "OCR-Status:" in html)
t("Freigegeben-Option in HTML", "freigegeben" in html)
t("Neu-OCR-Option in HTML", "neu_ocr" in html)
t("Ausschliessen-Option in HTML", "ausschliessen" in html)
t("Zurueckstellen-Option in HTML", "zurueckstellen" in html)
t("Grenzen in HTML", "Keine Originaländerung" in html)
t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())

# Status-JSON
print("\n--- Status-JSON ---")
status_json = {}
if (SB / "02_Status" / "UI03_1d_OCR_FREIGABEABLAUF.json").exists():
    status_json = json.loads((SB / "02_Status" / "UI03_1d_OCR_FREIGABEABLAUF.json").read_text(encoding="utf-8"))

t("Status-JSON hat modul", bool(status_json.get("modul")))
t("Status-JSON hat version", bool(status_json.get("version")))
t("Status-JSON hat seiten", isinstance(status_json.get("seiten"), int))
t("Status-JSON hat dokumente", isinstance(status_json.get("dokumente"), int))
t("Status-JSON hat freigabe_optionen", isinstance(status_json.get("freigabe_optionen"), list))
t("CORE11_konform Flag", status_json.get("core11_konform") == True)

# Grenzen
print("\n--- Grenzen ---")
t("Keine DB-Datei", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))
t("Keine ENV-Datei", not any(SB.rglob(".env*")))
t("Keine Cloud-URL in HTML", "http://" not in html.lower() and "https://" not in html.lower())

print(f"\nBESTANDEN: {ok}/{ges}")
if FEHLER:
    print("FEHLER:")
    for f in FEHLER:
        print(f"  - {f}")

sys.exit(0 if ok == ges else 1)
