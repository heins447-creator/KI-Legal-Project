#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI08 – Check-Datei: Posteingang / Importstrecke
Prüft: Config, Bereiche, Sperrregister, Demo-Modus, Runner-Struktur
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
    print("UI08 POSTEINGANG / IMPORTSTRECKE – CHECK")
    print("=" * 60)

    # 1. Config
    print("\n[1] Config-Prüfung")
    cfg = load_json("Config/ui08_posteingang_importstrecke_v1.json")
    t("modul_id == UI08", cfg.get("modul_id") == "UI08")
    t("betriebsmodus == demo", cfg.get("betriebsmodus") == "demo")
    t("produktiv_freigegeben == False", cfg.get("produktiv_freigegeben") is False)
    t("warnung vorhanden", len(cfg.get("warnung", "")) > 10)
    t("version_status == entwicklung", cfg.get("version_status") == "entwicklung")

    # 2. Bereiche
    print("\n[2] Anzeige-Bereiche")
    bereiche = cfg.get("anzeige_bereiche", [])
    t("bereiche definiert", len(bereiche) > 0)
    for b in bereiche:
        bid = b.get("id", "?")
        t(f"{bid} hat name", len(b.get("name", "")) > 0)
        t(f"{bid} hat farbe", len(b.get("farbe", "")) > 0)

    # 3. Abhängigkeiten
    print("\n[3] Abhängigkeiten")
    abh = cfg.get("abhaengigkeiten", {})
    t("datenbank definiert", len(abh.get("datenbank", "")) > 0)
    t("posteingang_verzeichnis definiert", len(abh.get("posteingang_verzeichnis", "")) > 0)
    t("bestehende_module definiert", len(abh.get("bestehende_module", [])) > 0)

    # 4. Sperrregister
    print("\n[4] Sperrregister-Prüfung")
    sperr = cfg.get("sperrregister_pruefung", {})
    t("sperrregister aktiv", sperr.get("aktiv") is True)
    t("sperrregister pfad gesetzt", len(sperr.get("pfad", "")) > 0)

    # 5. Demo-Modus
    print("\n[5] Demo-Modus")
    demo = cfg.get("demo_modus", {})
    t("nur_musterdaten == True", demo.get("nur_musterdaten") is True)
    t("echte_daten_erlaubt == False", demo.get("echte_daten_erlaubt") is False)
    t("max_dokumente begrenzt", demo.get("max_dokumente", 999) < 20)

    # 6. Ausgabe
    print("\n[6] Ausgabekonfiguration")
    aus = cfg.get("ausgabe", {})
    t("html_posteingang_uebersicht definiert", "html_posteingang_uebersicht" in aus)
    t("json_status definiert", "json_status" in aus)
    t("bericht definiert", "bericht" in aus)

    # 7. Python-Runner
    print("\n[7] Python-Runner UI08")
    runner_pfad = "Scripts/python_runner/ui08_posteingang_importstrecke.py"
    t("runner existiert", os.path.isfile(runner_pfad))
    if os.path.isfile(runner_pfad):
        with open(runner_pfad, "r", encoding="utf-8") as f:
            rc = f.read()
        t("runner hat hauptlauf", "def hauptlauf():" in rc)
        t("runner hat selbsttest", "def selbsttest():" in rc)
        t("runner prueft sperrregister", "pruefe_sperrregister" in rc)
        t("runner liest duckdb", "lese_duckdb_tabellen" in rc)
        t("runner liest json", "lese_json_karten" in rc)
        t("runner erzeugt html", "generiere_html" in rc)
        t("runner erzeugt json", "generiere_status_json" in rc)
        t("demo im html", "demo-banner" in rc)

    print("\n" + "=" * 60)
    print(f"ERGEBNIS: {'OK' if FEHLER == 0 else 'FEHLER'} ({FEHLER} Fehler, {WARNUNGEN} Warnungen)")
    print("=" * 60)
    return FEHLER == 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
