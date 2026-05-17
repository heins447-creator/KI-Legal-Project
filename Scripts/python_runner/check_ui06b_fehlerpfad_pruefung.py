#!/usr/bin/env python3
"""Prüfdatei für UI06b – Fehlerpfadprüfung"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI06b_Fehlerpfad_Pruefung"

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

print("UI06b PRÜFDATEI ======================================")

# Datei-Existenz
print("\n--- Dateien ---")
t("Status JSON", (SB / "02_Status" / "UI06b_FEHLERPFAD_STATUS.json").exists())
for key in ["A", "B", "C", "D", "E"]:
    t(f"Szenario {key} JSON", (SB / "02_Status" / f"UI06b_Szenario_{key}.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI06b_BERICHT.txt").exists())
t("Manifest", (SB / "07_Manifest" / "UI06b_MANIFEST.json").exists())
t("index.html", (SB / "11_Browseransicht" / "index.html").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "11_Browseransicht" / "index.html").exists():
    html = (SB / "11_Browseransicht" / "index.html").read_text(encoding="utf-8")

t("Alle Szenarien im HTML", all(f"Szenario {k}" in html for k in ["A", "B", "C", "D", "E"]))
t("Zusammenfassung im HTML", "Zusammenfassung" in html)
t("Tabelle in Zusammenfassung", "<table" in html)
t("Kein Internet/Cloud", "http://" not in html.lower() and "https://" not in html.lower())

# JSON-Inhalt
print("\n--- JSON-Inhalt ---")
status = {}
if (SB / "02_Status" / "UI06b_FEHLERPFAD_STATUS.json").exists():
    status = json.loads((SB / "02_Status" / "UI06b_FEHLERPFAD_STATUS.json").read_text(encoding="utf-8"))
t("5 Szenarien", len(status.get("szenarien", [])) == 5)
t("Ergebnisse vorhanden", len(status.get("ergebnisse", {})) == 5)

# Szenario-Prüfungen
print("\n--- Szenarien ---")
for key in ["A", "B", "C", "D", "E"]:
    s = load_json(SB / "02_Status" / f"UI06b_Szenario_{key}.json") or {}
    t(f"S{key}: Posteingang", "posteingang" in s)
    t(f"S{key}: Türschwelle", "tuerschwelle" in s)
    t(f"S{key}: Mandantenakte", "mandantenakte" in s)
    t(f"S{key}: Arbeitszentrale", "arbeitszentrale" in s)
    
    if s:
        tuer = s.get("tuerschwelle", {})
        mand = s.get("mandantenakte", {})
        arb = s.get("arbeitszentrale", {})
        
        if tuer.get("entscheidung") == "annehmen":
            t(f"S{key}: OCR-Status", "ocr_status" in mand)
            t(f"S{key}: Aktionen", "naechste_aktionen" in arb)

# Grenzen
print("\n--- Grenzen ---")
t("Keine DB-Datei", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))

print(f"\nBESTANDEN: {ok}/{ges}")
if FEHLER:
    print("FEHLER:")
    for f in FEHLER:
        print(f"  - {f}")

sys.exit(0 if ok == ges else 1)
