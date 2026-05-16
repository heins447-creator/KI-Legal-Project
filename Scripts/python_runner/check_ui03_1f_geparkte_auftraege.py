#!/usr/bin/env python3
"""Prüfdatei für UI03-1f Geparkte Aufträge verwalten (CORE-11-konform)."""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
SB = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "25_Geparkte_Auftraege_UI03_1f"

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

print("UI03-1f GEPARKTE AUFTRÄGE PRÜFDATEI ==================================")

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

# Ausgaben
print("\n--- Ausgaben ---")
t("Verwaltungs-HTML", (SB / "02_Status" / "UI03_1f_GEPARKTE_AUFTRAEGE.html").exists())
t("Status-JSON", (SB / "02_Status" / "UI03_1f_GEPARKTE_AUFTRAEGE.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI03_1f_GEPARKTE_AUFTRAEGE_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI03_1f_GEPARKTE_AUFTRAEGE_FEHLER.txt").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "02_Status" / "UI03_1f_GEPARKTE_AUFTRAEGE.html").exists():
    html = (SB / "02_Status" / "UI03_1f_GEPARKTE_AUFTRAEGE.html").read_text(encoding="utf-8")

t("HTML enthält Status-Banner", "status-banner" in html)
t("HTML enthält Gesamtübersicht", "gesamt-stats" in html)
t("HTML enthält Auftragsliste", "auftrags-karte" in html or "Keine geparkten Aufträge" in html)
t("HTML enthält Argos-Info", "ARGOS" in html.upper())
t("HTML enthält Parkgrund", "Parkgrund" in html)
t("HTML enthält Seiten-Stats", "seiten-stats" in html or "mini-stat" in html)
t("HTML enthält Grenzen", "Keine Originaländerung" in html)
t("Keine Cloud-Referenz", "http://" not in html.lower() and "https://" not in html.lower())

# Status-JSON
print("\n--- Status-JSON ---")
status_json = {}
if (SB / "02_Status" / "UI03_1f_GEPARKTE_AUFTRAEGE.json").exists():
    status_json = json.loads((SB / "02_Status" / "UI03_1f_GEPARKTE_AUFTRAEGE.json").read_text(encoding="utf-8"))

t("Status-JSON hat modul", bool(status_json.get("modul")))
t("Status-JSON hat version", bool(status_json.get("version")))
t("Status-JSON hat geparkte_auftraege", isinstance(status_json.get("geparkte_auftraege"), int))
t("Status-JSON hat argos_status", bool(status_json.get("argos_status")))
t("Status-JSON hat wartet_auf_modelle", isinstance(status_json.get("wartet_auf_modelle"), bool))
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
