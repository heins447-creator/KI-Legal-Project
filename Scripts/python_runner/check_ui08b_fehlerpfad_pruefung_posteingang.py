#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHECK UI08b – Fehlerpfadprüfung / Plausibilitätsprüfung Posteingang
Prüft: Config-Struktur, Sperrregister, Runner-Existenz, 9 Fehlerpfade, Schweregrade
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
    print("CHECK UI08b – Fehlerpfadprüfung Posteingang")
    print("=" * 60)

    cfg_pfad = "Config/ui08b_fehlerpfad_pruefung_posteingang_v1.json"
    runner_pfad = "Scripts/python_runner/ui08b_fehlerpfad_pruefung_posteingang.py"
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
        t("modul_id == UI08b", cfg.get("modul_id") == "UI08b")
        t("modulname vorhanden", bool(cfg.get("modulname")))
        t("version vorhanden", bool(cfg.get("version")))
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)
        t("echte_daten_erlaubt == false", cfg.get("echte_daten_erlaubt") is False)

        # 4. Fehlerpfade
        fehlerpfade = cfg.get("fehlerpfade", [])
        t("Genau 9 Fehlerpfade definiert", len(fehlerpfade) == 9)

        erwartete_ids = [f"FEHLER_{i:02d}" for i in range(1, 10)]
        tats_ids = [fp.get("id") for fp in fehlerpfade]
        t("Fehlerpfad-IDs lückenlos FEHLER_01..09", tats_ids == erwartete_ids)

        # 5. Jeder Fehlerpfad hat Name, Beschreibung, Schwere
        alle_vollstaendig = all(
            fp.get("name") and fp.get("beschreibung") and fp.get("schwere")
            for fp in fehlerpfade
        )
        t("Alle Fehlerpfade haben Name+Beschreibung+Schwere", alle_vollstaendig)

        # 6. Schweregrade gültig
        erlaubt = {"KRITISCH", "HOCH", "MITTEL"}
        schweren_ok = all(fp.get("schwere") in erlaubt for fp in fehlerpfade)
        t("Alle Schweregrade gültig (KRITISCH/HOCH/MITTEL)", schweren_ok)

        # 7. Mindestens ein Prüfmechanismus pro Fehlerpfad
        pruefung_ok = all(
            fp.get("db_pruefung") or fp.get("json_pruefung") or fp.get("datei_pruefung")
            for fp in fehlerpfade
        )
        t("Jeder Fehlerpfad hat DB- oder JSON- oder Datei-Prüfung", pruefung_ok)

        # 8. Ausgabepfade definiert
        ausgabe = cfg.get("ausgabe", {})
        t("html_fehlerpfad_uebersicht definiert", bool(ausgabe.get("html_fehlerpfad_uebersicht")))
        t("json_status definiert", bool(ausgabe.get("json_status")))
        t("bericht definiert", bool(ausgabe.get("bericht")))

        # 9. Sperrregister-Prüfung aktiv
        t("Sperrregister-Prüfung aktiv", cfg.get("register_pruefung", {}).get("sperrregister") is True)

    # 10. Sperrregister lesen
    if os.path.exists(sperrregister_pfad):
        try:
            with open(sperrregister_pfad, "r", encoding="utf-8") as f:
                sperr = json.load(f)
            eintraege = sperr.get("eintraege", [])
            ui08b_eintraege = [e for e in eintraege if e.get("modul_id") == "UI08b"]
            tw("UI08b im Sperrregister eingetragen", len(ui08b_eintraege) > 0)
            if ui08b_eintraege:
                e = ui08b_eintraege[0]
                t("UI08b gesperrt (produktiv)", e.get("gesperrt") is True)
                t("UI08b freigabe_erfordert nicht leer", len(e.get("freigabe_erfordert", [])) > 0)
        except Exception as e:
            t("Sperrregister lesbar", False)
            print(f"    -> {e}")
    else:
        tw("Sperrregister existiert", False)

    # 11. Runner-Selbsttest (Import + Funktionsprüfung)
    if os.path.exists(runner_pfad):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("ui08b_runner", runner_pfad)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            t("Runner importierbar", True)
            t("pruefe_fehlerpfad() definiert", hasattr(mod, "pruefe_fehlerpfad"))
            t("lese_duckdb_fehler() definiert", hasattr(mod, "lese_duckdb_fehler"))
            t("lese_json_fehler() definiert", hasattr(mod, "lese_json_fehler"))
            t("generiere_html() definiert", hasattr(mod, "generiere_html"))
            t("hauptlauf() definiert", hasattr(mod, "hauptlauf"))
            t("selbsttest() definiert", hasattr(mod, "selbsttest"))
        except Exception as e:
            t("Runner importierbar", False)
            print(f"    -> {e}")

    # 12. Zusammenfassung
    print("\n" + "=" * 60)
    if FEHLER == 0:
        print(f"CHECK UI08b BESTANDEN – {WARNUNGEN} Warnung(en)")
    else:
        print(f"CHECK UI08b FEHLGESCHLAGEN – {FEHLER} Fehler, {WARNUNGEN} Warnung(en)")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
