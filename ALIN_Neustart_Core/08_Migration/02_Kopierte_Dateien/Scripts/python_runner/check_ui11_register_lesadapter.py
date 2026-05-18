#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHECK UI11 – Register-Leseadapter
Prueft: Config-Struktur, Freeze-Kompatibilitaet, Sperrregister, Runner-Existenz, Register-Pfade
"""

import json, os, sys

FEHLER = 0
WARNUNGEN = 0

def t(bez, bed):
    global FEHLER, WARNUNGEN
    if bed:
        print(f"  [OK]   {bez}")
    else:
        print(f"  [FEHLER] {bez}")
        FEHLER += 1

def tw(bez, bed):
    global WARNUNGEN
    if bed:
        print(f"  [OK]   {bez}")
    else:
        print(f"  [WARN] {bez}")
        WARNUNGEN += 1

def main():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("CHECK UI11 – Register-Leseadapter")
    print("=" * 60)
    
    cfg_pfad = "Config/ui11_register_lesadapter_v1.json"
    runner_pfad = "Scripts/python_runner/ui11_register_lesadapter.py"
    sperrregister_pfad = "ALIN_Neustart_Core/01_Register/sperrregister.json"
    
    # 1. Dateien existieren
    t("Config existiert", os.path.exists(cfg_pfad))
    t("Runner existiert", os.path.exists(runner_pfad))
    
    # 2. Config laden
    cfg = None
    if os.path.exists(cfg_pfad):
        try:
            with open(cfg_pfad, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            t("Config ist valides JSON", True)
        except Exception as e:
            t("Config ist valides JSON", False)
            print(f"    -> {e}")
    
    # 3. Pflichtfelder
    if cfg:
        t("modul_id == UI11", cfg.get("modul_id") == "UI11")
        t("modulname vorhanden", bool(cfg.get("modulname")))
        t("version vorhanden", bool(cfg.get("version")))
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)
        t("echte_daten_erlaubt == false", cfg.get("echte_daten_erlaubt") is False)
        
        # 4. Freeze-Kompatibilitaet
        adapter_cfg = cfg.get("adapter_konfiguration", {})
        t("adapter_konfiguration vorhanden", bool(adapter_cfg))
        freeze = adapter_cfg.get("freeze_kompatibilitaet", {})
        t("freeze.beruehrt_ui03_ui07b == false", freeze.get("beruehrt_ui03_ui07b") is False)
        t("freeze.nur_lesend == true", freeze.get("nur_lesend") is True)
        t("freeze.neue_dateien == true", freeze.get("neue_dateien") is True)
        
        # 5. Register-Abhaengigkeiten
        abhaengigkeiten = cfg.get("abhaengigkeiten", {})
        erwartete_register = [
            "sperrregister", "ressourcenregister", "skillregister", "toolregister",
            "quellen_adapter_register", "lizenzregister", "update_register", "modulregister"
        ]
        t("8 Register in abhaengigkeiten", len(abhaengigkeiten) >= 8)
        for reg in erwartete_register:
            t(f"{reg} Pfad definiert", reg in abhaengigkeiten and bool(abhaengigkeiten[reg]))
        
        # 6. Konsistenzregeln
        regeln = cfg.get("konsistenzregeln", [])
        t("Mindestens 3 Konsistenzregeln", len(regeln) >= 3)
        
        regel_ids = [r.get("regel_id") for r in regeln]
        t("Regel-IDs eindeutig", len(regel_ids) == len(set(regel_ids)))
        
        # 7. Ausgabepfade
        ausgabe = cfg.get("ausgabe", {})
        t("json_adapter definiert", bool(ausgabe.get("json_adapter")))
        t("html_register_uebersicht definiert", bool(ausgabe.get("html_register_uebersicht")))
        t("bericht definiert", bool(ausgabe.get("bericht")))
        t("konsistenz_log definiert", bool(ausgabe.get("konsistenz_log")))
        
        # 8. Grenzen
        grenzen = cfg.get("grenzen", {})
        t("nur_lesend_auf_ui03_ui07b == true", grenzen.get("nur_lesend_auf_ui03_ui07b") is True)
        t("keine_dateien_in_frozen_module == true", grenzen.get("keine_dateien_in_frozen_module") is True)
        
        # 9. Sperrregister-Pruefung aktiv
        t("Sperrregister-Pruefung aktiv", cfg.get("register_pruefung", {}).get("sperrregister") is True)
    
    # 10. Sperrregister
    if os.path.exists(sperrregister_pfad):
        try:
            with open(sperrregister_pfad, "r", encoding="utf-8") as f:
                sperr = json.load(f)
            eintraege = sperr.get("eintraege", [])
            ui11_eintraege = [e for e in eintraege if e.get("modul_id") == "UI11"]
            tw("UI11 im Sperrregister eingetragen", len(ui11_eintraege) > 0)
            if ui11_eintraege:
                e = ui11_eintraege[0]
                t("UI11 gesperrt (produktiv)", e.get("gesperrt") is True)
        except Exception as e:
            t("Sperrregister lesbar", False)
            print(f"    -> {e}")
    else:
        tw("Sperrregister existiert", False)
    
    # 11. Runner-Import
    if os.path.exists(runner_pfad):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("ui11_runner", runner_pfad)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            t("Runner importierbar", True)
            t("lade_register() definiert", hasattr(mod, "lade_register"))
            t("analysiere_register() definiert", hasattr(mod, "analysiere_register"))
            t("pruefe_konsistenz() definiert", hasattr(mod, "pruefe_konsistenz"))
            t("erstelle_adapter() definiert", hasattr(mod, "erstelle_adapter"))
            t("generiere_html() definiert", hasattr(mod, "generiere_html"))
            t("generiere_json() definiert", hasattr(mod, "generiere_json"))
            t("hauptlauf() definiert", hasattr(mod, "hauptlauf"))
            t("selbsttest() definiert", hasattr(mod, "selbsttest"))
        except Exception as e:
            t("Runner importierbar", False)
            print(f"    -> {e}")
    
    # 12. Zusammenfassung
    print("\n" + "=" * 60)
    if FEHLER == 0:
        print(f"CHECK UI11 BESTANDEN – {WARNUNGEN} Warnung(en)")
    else:
        print(f"CHECK UI11 FEHLGESCHLAGEN – {FEHLER} Fehler, {WARNUNGEN} Warnung(en)")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
