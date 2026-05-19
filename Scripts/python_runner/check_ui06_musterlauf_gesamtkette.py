#!/usr/bin/env python3
"""Prüfdatei für UI06 – Musterlauf Gesamtkette"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI06_Musterlauf_Gesamtkette"
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"

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

print("UI06 PRÜFDATEI =======================================")

# Datei-Existenz
print("\n--- Dateien ---")
t("Status JSON", (SB / "02_Status" / "UI06_MUSTERLAUF_STATUS.json").exists())
t("Station 1 Posteingang", (SB / "02_Status" / "UI06_01_POSTEINGANG.json").exists())
t("Station 2 Türschwelle", (SB / "02_Status" / "UI06_02_TUERSCHWELLE.json").exists())
t("Station 3 Mandantenakte", (SB / "02_Status" / "UI06_03_MANDANTENAKTE.json").exists())
t("Station 4 Arbeitszentrale", (SB / "02_Status" / "UI06_04_ARBEITSZENTRALE.json").exists())
t("UI03-1g kompatibel", (SB / "02_Status" / "UI03_1g_GESAMTANSICHT_STATUS.json").exists())
t("UI04b kompatibel", (SB / "02_Status" / "UI04b_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI06_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI06_FEHLER.txt").exists())
t("Manifest", (SB / "07_Manifest" / "UI06_MANIFEST.json").exists())
t("index.html", (SB / "11_Browseransicht" / "index.html").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "11_Browseransicht" / "index.html").exists():
    html = (SB / "11_Browseransicht" / "index.html").read_text(encoding="utf-8")

t("Akten-ID angezeigt", "Akten-ID" in html)
t("Station 1 Posteingang", "Posteingang" in html)
t("Station 2 Türschwelle", "Türschwelle" in html)
t("Station 3 Mandantenakte", "Mandantenakte" in html)
t("Station 4 Arbeitszentrale", "Arbeitszentrale" in html)
t("Pfeile zwischen Stationen", "⬇" in html)
t("OCR-Fehler markiert", "fehlerhaft" in html or "❌" in html)
t("Argos-Blockierung", "Argos" in html or "gesperrt" in html.lower())
t("Zulässige Aktionen", "zulässig" in html.lower() or "Nächste" in html)
t("Gesperrte Aktionen", "gesperrt" in html.lower() or "🔒" in html)
t("Kein Internet/Cloud", "http://" not in html.lower() and "https://" not in html.lower())

# JSON-Inhalt
print("\n--- JSON-Inhalt ---")
status = {}
if (SB / "02_Status" / "UI06_MUSTERLAUF_STATUS.json").exists():
    status = json.loads((SB / "02_Status" / "UI06_MUSTERLAUF_STATUS.json").read_text(encoding="utf-8"))
t("Status hat Stationen", "stationen" in status)
t("Status hat Zusammenfassung", "zusammenfassung" in status)
t("Status hat Grenzen", "grenzen" in status)

if status:
    z = status.get("zusammenfassung", {})
    t("Dokumente gezählt", z.get("dokumente", 0) > 0)
    t("OCR-Fehler gezählt", "ocr_fehler" in z)
    t("Übersetzung gesperrt-Flag", "uebersetzung_gesperrt" in z)
    t("Entscheidung vorhanden", bool(z.get("entscheidung")))
    t("Aktionen gezählt", "naechste_aktionen" in z)

# Stationen prüfen
print("\n--- Stationen ---")
s1 = load_json(SB / "02_Status" / "UI06_01_POSTEINGANG.json") or {}
s2 = load_json(SB / "02_Status" / "UI06_02_TUERSCHWELLE.json") or {}
s3 = load_json(SB / "02_Status" / "UI06_03_MANDANTENAKTE.json") or {}
s4 = load_json(SB / "02_Status" / "UI06_04_ARBEITSZENTRALE.json") or {}

t("S1: Akten-ID", bool(s1.get("akten_id")))
t("S1: Dokumente", len(s1.get("dokumente", [])) > 0)
t("S2: Mandatsfähig", "mandatsfaehig" in s2)
t("S2: Entscheidung", bool(s2.get("entscheidung")))
t("S3: OCR-Status", "ocr_status" in s3)
t("S3: Übersetzung", "uebersetzung" in s3)
t("S3: Freigabe", "freigabe" in s3)
t("S3: Parkstatus", "parkstatus" in s3)
t("S4: UI03-Status", "ui03" in s4)
t("S4: UI04b-Status", "ui04b" in s4)
t("S4: Aktionen", "naechste_aktionen" in s4)
t("S4: Sperrregister", s4.get("sperrregister_pruefung", False))

# Sperrregister
print("\n--- Sperrregister ---")
sperrregister_path = CORE / "sperrregister.json"
t("Sperrregister existiert", sperrregister_path.exists())
if sperrregister_path.exists():
    sperr = json.loads(sperrregister_path.read_text(encoding="utf-8"))
    eintraege = sperr.get("eintraege", [])
    t("Sperrregister hat Einträge", len(eintraege) >= 2)

# Grenzen
print("\n--- Grenzen ---")
t("Keine DB-Datei", not any(SB.rglob("*.db")) and not any(SB.rglob("*.duckdb")))
t("Keine neue OCR-Ausgabe", "neue OCR" not in html.lower() or "Keine neue OCR" in html)

print(f"\nBESTANDEN: {ok}/{ges}")
if FEHLER:
    print("FEHLER:")
    for f in FEHLER:
        print(f"  - {f}")

sys.exit(0 if ok == ges else 1)
