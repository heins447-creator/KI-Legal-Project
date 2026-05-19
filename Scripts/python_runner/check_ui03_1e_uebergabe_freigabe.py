#!/usr/bin/env python3
"""Prüfdatei für UI03-1e Übergabe Freigabeentscheidung (CORE-11-konform)."""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "24_Uebergabe_Freigabe_UI03_1e"

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

print("UI03-1e ÜBERGABE FREIGABEENTSCHEIDUNG PRÜFDATEI =========================")

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
    t("Argos Sprachpaare im Ressourcenregister", any(r.startswith("ARGOS_") for r in ress))

# Ausgaben
print("\n--- Ausgaben ---")
t("Uebergabe-HTML", (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.html").exists())
t("Auftrag-JSON", (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.json").exists())
t("Status-JSON", (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI03_1e_UEBERGABE_FREIGABE_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI03_1e_UEBERGABE_FREIGABE_FEHLER.txt").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.html").exists():
    html = (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.html").read_text(encoding="utf-8")

t("HTML enthält Park-Banner", "AUFTRAG VORBEREITET" in html or "Auftrag bereit" in html)
t("HTML enthält Statistik", "gesamt-stats" in html)
t("HTML enthält Seiten-Karten", "seiten-karte" in html)
t("HTML enthält Radio-Buttons", 'type="radio"' in html)
t("HTML enthält 5 Kategorien", html.count('type="radio"') >= 5)
t("HTML enthält OCR-Vorschau", "ocr-vorschau" in html)
t("HTML enthält Ursprungs-Status", "ursprungs-status" in html)
t("HTML enthält Grenzen", "Keine Originaländerung" in html)
t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())

# Auftrag-JSON
print("\n--- Auftrag-JSON ---")
auftrag_json = {}
if (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.json").exists():
    auftrag_json = json.loads((SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE.json").read_text(encoding="utf-8"))

t("Auftrag hat auftrag_id", bool(auftrag_json.get("auftrag_id")))
t("Auftrag hat akten_id", bool(auftrag_json.get("akten_id")))
t("Auftrag hat status", bool(auftrag_json.get("status")))
t("Auftrag hat parkgrund", bool(auftrag_json.get("parkgrund")))
t("Auftrag hat seiten", isinstance(auftrag_json.get("seiten"), list))
t("Auftrag-Seiten haben kategorie", all("kategorie" in s for s in auftrag_json.get("seiten", [])))

# Status-JSON
print("\n--- Status-JSON ---")
status_json = {}
if (SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE_STATUS.json").exists():
    status_json = json.loads((SB / "02_Status" / "UI03_1e_UEBERGABE_FREIGABE_STATUS.json").read_text(encoding="utf-8"))

t("Status-JSON hat modul", bool(status_json.get("modul")))
t("Status-JSON hat version", bool(status_json.get("version")))
t("Status-JSON hat auftrag", bool(status_json.get("auftrag")))
t("Status-JSON hat argos_verfuegbar", isinstance(status_json.get("argos_verfuegbar"), bool))
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
