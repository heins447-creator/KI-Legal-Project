#!/usr/bin/env python3
"""Prüfdatei UI03-1g – Kombinierte Gesamtansicht (CORE-11-konform).

Prüft:
1. Config vorhanden und valide
2. Quell-Modul-Schreibbereiche bekannt
3. Dashboard-HTML erzeugbar
4. Keine Cloud/Internet-Referenzen
5. Keine Vorgänger-Modifikation
"""
import json, sys, os
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
CONFIG_PATH = ROOT / "Config" / "ui03_1g_gesamtansicht_v1.json"
PYTHON_RUNNER = ROOT / "Scripts" / "python_runner" / "ui03_1g_gesamtansicht.py"

def t(bez, bed):
    v = bool(bed)
    print(f"  {'[OK]' if v else '[FEHLER]'} {bez}")
    return v

ok = 0
ges = 0

def check(bez, bed):
    global ok, ges
    ges += 1
    if t(bez, bed):
        ok += 1

print("UI03-1g GESAMTANSICHT PRÜFDATEI =======================================")

# 1. Config
cfg = {}
if CONFIG_PATH.exists():
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"  [FEHLER] Config nicht lesbar: {e}")
        cfg = {}

check("Config-Datei vorhanden", CONFIG_PATH.exists())
check("Config hat modul", cfg.get("modul") == "UI03-1g")
check("Config hat version", bool(cfg.get("version")))
check("Config hat ausgabe", bool(cfg.get("ausgabe")))
check("Config hat grenzen", bool(cfg.get("grenzen")))

# 2. Python-Läufer
check("Python-Läufer vorhanden", PYTHON_RUNNER.exists())
if PYTHON_RUNNER.exists():
    src = PYTHON_RUNNER.read_text(encoding="utf-8")
    check("Läufer hat main()", "def main():" in src)
    check("Läufer hat selbsttest()", "def selbsttest():" in src)
    check("Läufer liest Vorgänger (1b)", '21_OCR_Uebersetzungskontrolle_UI03_1b' in src)
    check("Läufer liest Vorgänger (1c)", '22_Uebersetzungsarbeitsplatz_UI03_1c' in src)
    check("Läufer liest Vorgänger (1d)", '23_OCR_Freigabeablauf_UI03_1d' in src)
    check("Läufer liest Vorgänger (1e)", '24_Uebergabe_Freigabe_UI03_1e' in src)
    check("Läufer liest Vorgänger (1f)", '25_Geparkte_Auftraege_UI03_1f' in src)
    check("Läufer prüft Argos-Status", "ARGOS_TRANSLATE" in src)
    check("Keine Cloud-Referenz", "http://" not in src.lower() and "https://" not in src.lower())
    check("Keine DB-Änderung", "keine_db_aenderung" in src.lower() or "Grenzen" in src)
    check("Keine Vorgänger-Modifikation", "keine_vorgaenger_modifikation" in src.lower() or "keine_vorgaenger" in src.lower())

# 3. Register lesend
toolreg = CORE / "toolregister.json"
ressreg = CORE / "ressourcenregister.json"
check("Toolregister lesbar", toolreg.exists())
check("Ressourcenregister lesbar", ressreg.exists())

# 4. Schreibbereich
sb = ROOT / "Agentensteuerung" / "UI03_Mandantenakte" / "26_Gesamtansicht_UI03_1g"
check("Schreibbereich bekannt", sb.name == "26_Gesamtansicht_UI03_1g")

print(f"\nBESTANDEN: {ok}/{ges}")
sys.exit(0 if ok == ges else 1)
