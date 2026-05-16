#!/usr/bin/env python3
"""Prüfdatei für UI03-1b OCR-/Übersetzungskontrolle (CORE-11-konform)."""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "21_OCR_Uebersetzungskontrolle_UI03_1b"

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

print("UI03-1b OCR-KONTROLLE PRÜFDATEI =======================================")

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
    t("Argos Translate im Toolregister", "ARGOS_TRANSLATE" in tools)

if (CORE / "ressourcenregister.json").exists():
    rr = json.loads((CORE / "ressourcenregister.json").read_text(encoding="utf-8-sig"))
    ress = [r.get("resource_id") for r in rr.get("eintraege", []) if r.get("resource_id")]
    t("DEEPL_API im Ressourcenregister", any("DEEPL" in r for r in ress))
    t("Argos Sprachpaare im Ressourcenregister", any(r.startswith("ARGOS_") for r in ress))

# Ausgaben
print("\n--- Ausgaben ---")
t("Status-HTML", (SB / "02_Status" / "UI03_1b_OCR_KONTROLLE_STATUS.html").exists())
t("Status-JSON", (SB / "02_Status" / "UI03_1b_OCR_KONTROLLE_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI03_1b_OCR_KONTROLLE_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI03_1b_OCR_KONTROLLE_FEHLER.txt").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "02_Status" / "UI03_1b_OCR_KONTROLLE_STATUS.html").exists():
    html = (SB / "02_Status" / "UI03_1b_OCR_KONTROLLE_STATUS.html").read_text(encoding="utf-8")

t("HTML enthält Tabelle", "<table>" in html)
t("HTML enthält Dreiansicht", "dreiansicht" in html)
t("Tesseract-Status in HTML", "Tesseract" in html)
t("Argos-Status in HTML", "Argos" in html)
t("DEEPL-Status in HTML", "DEEPL" in html)
t("Freigegeben-Badge", "FREIGEGEBEN" in html)
t("Gesperrt-Badge", "GESPERRT" in html)
t("Grenzen in HTML", "Keine Originaländerung" in html)
t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())
t("Sprachpaare in HTML", "Argos-Sprachpaare" in html)

# Status-JSON
print("\n--- Status-JSON ---")
status_json = {}
if (SB / "02_Status" / "UI03_1b_OCR_KONTROLLE_STATUS.json").exists():
    status_json = json.loads((SB / "02_Status" / "UI03_1b_OCR_KONTROLLE_STATUS.json").read_text(encoding="utf-8"))

t("Status-JSON hat modul", bool(status_json.get("modul")))
t("Status-JSON hat version", bool(status_json.get("version")))
t("Status-JSON hat register_pruefung", bool(status_json.get("register_pruefung")))
t("Status-JSON hat grenzen", bool(status_json.get("grenzen")))
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
