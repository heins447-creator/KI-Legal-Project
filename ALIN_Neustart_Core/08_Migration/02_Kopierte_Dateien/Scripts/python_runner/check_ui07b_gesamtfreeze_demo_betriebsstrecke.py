#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI07b – Check-Datei: Gesamtfreeze Demo-Betriebsstrecke
Prüft: Config, Freeze-Status, Modul-Liste, Ausgabe, Runner-Struktur
"""

import json, os, sys

FEHLER = 0
WARNUNGEN = 0

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def t(bez, bed):
    global FEHLER
    if not bed:
        FEHLER += 1
        print(f"  [FAIL] {bez}")
    else:
        print(f"  [OK]   {bez}")

def main():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI07b GESAMTFREEZE – CHECK")
    print("=" * 60)

    # 1. Config
    print("\n[1] Config-Prüfung")
    cfg = load_json("Config/ui07b_gesamtfreeze_demo_betriebsstrecke_v1.json")
    t("modul_id == UI07b", cfg.get("modul_id") == "UI07b")
    t("freeze_status == eingefroren", cfg.get("freeze_status") == "eingefroren")
    t("freeze_datum gesetzt", len(cfg.get("freeze_datum", "")) > 0)
    t("produktiv_freigegeben == False", cfg.get("produktiv_freigegeben") is False)
    t("warnung vorhanden", len(cfg.get("warnung", "")) > 10)
    t("version_status == freeze", cfg.get("version_status") == "freeze")
    t("betriebsmodus == demo", cfg.get("betriebsmodus") == "demo")

    # 2. Module
    print("\n[2] Modul-Liste")
    module = cfg.get("strecke_ui03_bis_ui07", {}).get("module", [])
    t("module definiert", len(module) > 0)
    ids = [m["id"] for m in module]
    t("UI03-1b enthalten", "UI03-1b" in ids)
    t("UI03-1c enthalten", "UI03-1c" in ids)
    t("UI03-1d enthalten", "UI03-1d" in ids)
    t("UI03-1e enthalten", "UI03-1e" in ids)
    t("UI03-1f enthalten", "UI03-1f" in ids)
    t("UI03-1g enthalten", "UI03-1g" in ids)
    t("UI04b enthalten", "UI04b" in ids)
    t("UI05 enthalten", "UI05" in ids)
    t("UI06 enthalten", "UI06" in ids)
    t("UI06b enthalten", "UI06b" in ids)
    t("UI07 enthalten", "UI07" in ids)

    # 3. Dateipfade pro Modul
    print("\n[3] Dateipfade pro Modul")
    for m in module:
        for key in ["config", "runner", "check", "starter", "doku"]:
            if key in m:
                t(f"{m['id']} {key} existiert", os.path.isfile(m[key]))

    # 4. Ergänzende Dateien
    print("\n[4] Ergänzende Dateien")
    erg_doku = cfg.get("strecke_ui03_bis_ui07", {}).get("ergaenzende_doku", [])
    erg_runner = cfg.get("strecke_ui03_bis_ui07", {}).get("ergaenzende_runner", [])
    for d in erg_doku:
        t(f"Doku {os.path.basename(d)} existiert", os.path.isfile(d))
    for r in erg_runner:
        t(f"Runner {os.path.basename(r)} existiert", os.path.isfile(r))

    # 5. Freeze-Regeln
    print("\n[5] Freeze-Regeln")
    regeln = cfg.get("freeze_regeln", [])
    t("freeze_regeln definiert", len(regeln) > 0)
    t("keine_aenderungen_regel", any("Keine Änderungen" in r for r in regeln))
    t("keine_neue_fachlogik_regel", any("neue Fachlogik" in r for r in regeln))

    # 6. Ausgabe
    print("\n[6] Ausgabekonfiguration")
    aus = cfg.get("ausgabe", {})
    t("html_freeze_uebersicht definiert", "html_freeze_uebersicht" in aus)
    t("json_status definiert", "json_status" in aus)
    t("bericht definiert", "bericht" in aus)

    # 7. Python-Runner
    print("\n[7] Python-Runner UI07b")
    runner_pfad = "Scripts/python_runner/ui07b_gesamtfreeze_demo_betriebsstrecke.py"
    t("runner existiert", os.path.isfile(runner_pfad))
    if os.path.isfile(runner_pfad):
        with open(runner_pfad, "r", encoding="utf-8") as f:
            rc = f.read()
        t("runner hat hauptlauf", "def hauptlauf():" in rc)
        t("runner hat selbsttest", "def selbsttest():" in rc)
        t("runner prueft module", "pruefe_modul" in rc)
        t("runner prueft git_status", "git_status_datei" in rc)
        t("runner erzeugt html", "generiere_html" in rc)
        t("runner erzeugt json", "generiere_status_json" in rc)
        t("runner erzeugt bericht", "schreibe_bericht" in rc)
        t("freeze im html", "freeze-banner" in rc)
        t("keine fachlogik", "KEINE neue Fachlogik" in rc)

    print("\n" + "=" * 60)
    print(f"ERGEBNIS: {'OK' if FEHLER == 0 else 'FEHLER'} ({FEHLER} Fehler, {WARNUNGEN} Warnungen)")
    print("=" * 60)
    return FEHLER == 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
