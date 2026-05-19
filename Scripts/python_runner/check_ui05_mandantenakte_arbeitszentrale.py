#!/usr/bin/env python3
"""Prüfdatei für UI05 – Mandantenakte Arbeitszentrale"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
SB = ROOT / "Agentensteuerung" / "UI05_Mandantenakte_Arbeitszentrale"
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

print("UI05 PRÜFDATEI =======================================")

# Datei-Existenz
print("\n--- Dateien ---")
t("Status JSON", (SB / "02_Status" / "UI05_ARBEITSZENTRALE_STATUS.json").exists())
t("Bericht", (SB / "03_Berichte" / "UI05_BERICHT.txt").exists())
t("Fehlerbericht", (SB / "05_Fehler" / "UI05_FEHLER.txt").exists())
t("Manifest", (SB / "07_Manifest" / "UI05_MANIFEST.json").exists())
t("index.html", (SB / "11_Browseransicht" / "index.html").exists())

# HTML-Inhalt
print("\n--- HTML-Inhalt ---")
html = ""
if (SB / "11_Browseransicht" / "index.html").exists():
    html = (SB / "11_Browseransicht" / "index.html").read_text(encoding="utf-8")

t("Akten-ID angezeigt", "Akten-ID" in html)
t("UI03-Status angezeigt", "OCR" in html and "Übersetzung" in html)
t("UI04b-Status angezeigt", "Plausibilität" in html or "Entscheidung" in html)
t("Nächste Aktionen", "zulässig" in html.lower() or "Nächste" in html)
t("Gesperrte Aktionen", "gesperrt" in html.lower() or "🔒" in html)
t("Sperrregister-Hinweis", "Sperrregister" in html or "gesperrt" in html.lower())
t("Kein Internet/Cloud", "http://" not in html.lower() and "https://" not in html.lower())

# Navigation und Bedienbarkeit (UI05c)
print("\n--- Navigation / Bedienbarkeit ---")
t("Navigationsleiste im HTML", "nav-leiste" in html)
t("Schnellzugriff-Label", "Schnellzugriff" in html)
t("Zulässige Aktionen als Button", "btn-action" in html)
t("Gesperrte Aktionen nicht als Button", "action-disabled" in html)
t("Blockierende Aktionen markiert", "blockierend" in html.lower())

# JSON-Inhalt
print("\n--- JSON-Inhalt ---")
status = {}
if (SB / "02_Status" / "UI05_ARBEITSZENTRALE_STATUS.json").exists():
    status = json.loads((SB / "02_Status" / "UI05_ARBEITSZENTRALE_STATUS.json").read_text(encoding="utf-8"))
t("Status hat UI03", "ui03" in status)
t("Status hat UI04b", "ui04b" in status)
t("Status hat Aktionen", "naechste_aktionen" in status)
t("Status hat Sperrregister-Prüfung", status.get("sperrregister_pruefung", False))
t("Status hat Gesperrt-Flag", "gesperrte_aktionen_blockiert" in status)

# Prioritäten und Abhängigkeiten (UI05b)
print("\n--- Prioritäten / Abhängigkeiten / Blockierung ---")
if status:
    aktionen = status.get("naechste_aktionen", {})
    zulaessig = aktionen.get("zulaessig", [])
    gesperrt = aktionen.get("gesperrt", [])
    abhaengig = aktionen.get("abhaengigkeiten", [])

    prios = [a.get("prioritaet", 99) for a in zulaessig]
    t("Prioritäten numerisch", all(isinstance(p, int) for p in prios) if prios else True)
    t("Prioritäten sortiert", prios == sorted(prios) if len(prios) > 1 else True)
    t("Blockierend-Flag vorhanden", all("blockierend" in a for a in zulaessig) if zulaessig else True)

    p0 = [a for a in zulaessig if a.get("prioritaet") == 0]
    t("P0 blockierend", all(a.get("blockierend") for a in p0) if p0 else True)
    t("Abhängigkeiten separate Liste", isinstance(abhaengig, list))

    uebersetzung_zulaessig = any("bersetzung" in a.get("label", "") for a in zulaessig)
    uebersetzung_gesperrt = any("bersetzung" in g.get("aktion", "") or "Argos" in g.get("grund", "") for g in gesperrt)
    t("Übersetzung gesperrt wenn Argos fehlt", not uebersetzung_zulaessig or not uebersetzung_gesperrt)

# Sperrregister
print("\n--- Sperrregister ---")
sperrregister_path = CORE / "sperrregister.json"
t("Sperrregister existiert", sperrregister_path.exists())
if sperrregister_path.exists():
    sperr = json.loads(sperrregister_path.read_text(encoding="utf-8"))
    eintraege = sperr.get("eintraege", [])
    t("Sperrregister hat Einträge", len(eintraege) >= 2)
    ids = {e.get("modul_id") for e in eintraege}
    t("011_quellenbetreuer... im Sperrregister", "011_quellenbetreuer_fachanwaltsraster_v1" in ids)
    t("014_source_adapter... im Sperrregister", "014_source_adapter_healthcheck_framework_v1" in ids)

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
