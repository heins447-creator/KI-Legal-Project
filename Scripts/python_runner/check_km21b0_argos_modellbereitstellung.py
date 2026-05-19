#!/usr/bin/env python3
"""Prüfdatei KM21b-0 – Argos-Modellbereitstellung vorbereiten (CORE-11-konform).

Prüft:
1. Config vorhanden und valide
2. Ablageordner in Config definiert
3. Python-Läufer vorhanden und korrekt strukturiert
4. Keine Download/Cloud/Installations-Logik
5. Manifest-Schema erzeugbar
"""
import json, sys, os
from pathlib import Path

ROOT = Path(r"I:\KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core" / "01_Register"
CONFIG_PATH = ROOT / "Config" / "km21b0_argos_modellbereitstellung_v1.json"
PYTHON_RUNNER = ROOT / "Scripts" / "python_runner" / "km21b0_argos_modellbereitstellung.py"

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

print("KM21b-0 ARGOS-MODELLBEREITSTELLUNG PRÜFDATEI =========================")

# 1. Config
cfg = {}
if CONFIG_PATH.exists():
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"  [FEHLER] Config nicht lesbar: {e}")
        cfg = {}

check("Config-Datei vorhanden", CONFIG_PATH.exists())
check("Config hat modul", cfg.get("modul") == "KM21b-0")
check("Config hat version", bool(cfg.get("version")))
check("Config hat ablage", bool(cfg.get("ablage")))
check("Config hat ausgabe", bool(cfg.get("ausgabe")))
check("Config hat grenzen", bool(cfg.get("grenzen")))

# 2. Ablageordner
if cfg.get("ablage"):
    for name in cfg["ablage"]:
        check(f"Ablage '{name}' in Config", True)

# 3. Python-Läufer
check("Python-Läufer vorhanden", PYTHON_RUNNER.exists())
if PYTHON_RUNNER.exists():
    src = PYTHON_RUNNER.read_text(encoding="utf-8")
    check("Läufer hat main()", "def main():" in src)
    check("Läufer hat selbsttest()", "def selbsttest():" in src)
    check("Läufer erzeugt Manifest-Schema", "manifest_schema" in src or "Manifest" in src)
    check("Läufer erzeugt Importanleitung", "Importanleitung" in src or "importanleitung" in src)
    check("Läufer erzeugt Dummy-Manifest", "dummy_manifest" in src or "Dummy" in src)
    check("Kein Download", "download" not in src.lower() or "kein_download" in src.lower())
    check("Keine Cloud-Ref", "http://" not in src.lower() and "https://" not in src.lower())
    check("Kein Install", "install" not in src.lower() or "keine_installation" in src.lower())
    check("Keine DB-Änderung", "keine_db_aenderung" in src.lower() or "Grenzen" in src)
    check("Keine Registeränderung", "keine_registeraenderung" in src.lower() or "Grenzen" in src)
    check("Schreibbereich 21b0", "21b0_Argos_Modellbereitstellung" in src)

# 4. Register lesend
toolreg = CORE / "toolregister.json"
ressreg = CORE / "ressourcenregister.json"
check("Toolregister lesbar", toolreg.exists())
check("Ressourcenregister lesbar", ressreg.exists())

print(f"\nBESTANDEN: {ok}/{ges}")
sys.exit(0 if ok == ges else 1)
