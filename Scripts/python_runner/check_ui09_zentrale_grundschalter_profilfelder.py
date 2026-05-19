#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHECK UI09 – Zentrale Grundschalter und Profilfelder
Prüft: Config-Struktur, Sperrregister, Runner-Existenz, Profilfelder, Grundschalter, Validierungsregeln
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
    print("CHECK UI09 – Zentrale Grundschalter und Profilfelder")
    print("=" * 60)

    cfg_pfad = "Config/ui09_zentrale_grundschalter_profilfelder_v1.json"
    runner_pfad = "Scripts/python_runner/ui09_zentrale_grundschalter_profilfelder.py"
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
        t("modul_id == UI09", cfg.get("modul_id") == "UI09")
        t("modulname vorhanden", bool(cfg.get("modulname")))
        t("version vorhanden", bool(cfg.get("version")))
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)
        t("echte_daten_erlaubt == false", cfg.get("echte_daten_erlaubt") is False)

        # 4. Zentrales Profil
        profil = cfg.get("zentrales_profil", {})
        t("zentrales_profil vorhanden", bool(profil))
        t("profil_id gesetzt", bool(profil.get("profil_id")))
        t("profil_version gesetzt", bool(profil.get("profil_version")))

        felder = profil.get("felder", [])
        t("Mindestens 10 Profilfelder", len(felder) >= 10)

        # Pflichtfelder prüfen
        pflicht_ids = ["sprache_dokument", "sprache_anwalt", "akten_id", "sicherheitsstatus",
                       "freigabe_vorzimmer", "freigabe_anwalt", "freigabe_schlusskontrolle",
                       "betriebsmodus", "online_status", "mandant_id"]
        tats_ids = [f.get("feld_id") for f in felder]
        t("Alle Pflichtfelder vorhanden", all(pid in tats_ids for pid in pflicht_ids))

        # Jedes Feld hat Typ und Default
        felder_ok = all(f.get("feld_id") and f.get("typ") and "default" in f for f in felder)
        t("Alle Felder haben ID+Typ+Default", felder_ok)

        # 5. Grundschalter
        schalter = cfg.get("grundschalter", {}).get("schalter", [])
        t("Mindestens 5 Grundschalter", len(schalter) >= 5)

        gs_ids = ["GS01", "GS02", "GS03", "GS04", "GS05", "GS06", "GS07", "GS08"]
        tats_gs = [s.get("id") for s in schalter]
        t("Alle erwarteten GS-IDs vorhanden", all(gid in tats_gs for gid in gs_ids))

        gs07 = next((s for s in schalter if s.get("id") == "GS07"), None)
        t("GS07 Musterdaten-Modus hat default=true", gs07 is not None and gs07.get("default") is True)

        # 6. Validierungsregeln
        regeln = cfg.get("validierungsregeln", [])
        t("Mindestens 3 Validierungsregeln", len(regeln) >= 3)

        regel_ids = [r.get("regel_id") for r in regeln]
        t("Regel-IDs eindeutig", len(regel_ids) == len(set(regel_ids)))

        # 7. Ausgabepfade
        ausgabe = cfg.get("ausgabe", {})
        t("html_profiluebersicht definiert", bool(ausgabe.get("html_profiluebersicht")))
        t("json_profil definiert", bool(ausgabe.get("json_profil")))
        t("json_grundschalter definiert", bool(ausgabe.get("json_grundschalter")))
        t("bericht definiert", bool(ausgabe.get("bericht")))

        # 8. Sperrregister-Prüfung aktiv
        t("Sperrregister-Prüfung aktiv", cfg.get("register_pruefung", {}).get("sperrregister") is True)

    # 9. Sperrregister
    if os.path.exists(sperrregister_pfad):
        try:
            with open(sperrregister_pfad, "r", encoding="utf-8") as f:
                sperr = json.load(f)
            eintraege = sperr.get("eintraege", [])
            ui09_eintraege = [e for e in eintraege if e.get("modul_id") == "UI09"]
            tw("UI09 im Sperrregister eingetragen", len(ui09_eintraege) > 0)
            if ui09_eintraege:
                e = ui09_eintraege[0]
                t("UI09 gesperrt (produktiv)", e.get("gesperrt") is True)
        except Exception as e:
            t("Sperrregister lesbar", False)
            print(f"    -> {e}")
    else:
        tw("Sperrregister existiert", False)

    # 10. Runner-Import
    if os.path.exists(runner_pfad):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("ui09_runner", runner_pfad)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            t("Runner importierbar", True)
            t("validiere_profil() definiert", hasattr(mod, "validiere_profil"))
            t("validiere_grundschalter() definiert", hasattr(mod, "validiere_grundschalter"))
            t("generiere_html() definiert", hasattr(mod, "generiere_html"))
            t("generiere_json_profil() definiert", hasattr(mod, "generiere_json_profil"))
            t("generiere_json_schalter() definiert", hasattr(mod, "generiere_json_schalter"))
            t("generiere_bericht() definiert", hasattr(mod, "generiere_bericht"))
            t("hauptlauf() definiert", hasattr(mod, "hauptlauf"))
            t("selbsttest() definiert", hasattr(mod, "selbsttest"))
        except Exception as e:
            t("Runner importierbar", False)
            print(f"    -> {e}")

    # 11. Zusammenfassung
    print("\n" + "=" * 60)
    if FEHLER == 0:
        print(f"CHECK UI09 BESTANDEN – {WARNUNGEN} Warnung(en)")
    else:
        print(f"CHECK UI09 FEHLGESCHLAGEN – {FEHLER} Fehler, {WARNUNGEN} Warnung(en)")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
