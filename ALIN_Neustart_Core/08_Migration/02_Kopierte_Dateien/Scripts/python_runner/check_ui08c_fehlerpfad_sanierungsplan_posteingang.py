#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHECK UI08c – Fehlerpfad-Sanierungsplan Posteingang
Prüft: Config-Struktur, Sperrregister, Runner-Existenz, Sanierungsmatrix, Verantwortlichkeiten
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
    print("CHECK UI08c – Fehlerpfad-Sanierungsplan Posteingang")
    print("=" * 60)

    cfg_pfad = "Config/ui08c_fehlerpfad_sanierungsplan_posteingang_v1.json"
    runner_pfad = "Scripts/python_runner/ui08c_fehlerpfad_sanierungsplan_posteingang.py"
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
        t("modul_id == UI08c", cfg.get("modul_id") == "UI08c")
        t("modulname vorhanden", bool(cfg.get("modulname")))
        t("version vorhanden", bool(cfg.get("version")))
        t("produktiv_freigegeben == false", cfg.get("produktiv_freigegeben") is False)
        t("nur_musterdaten == true", cfg.get("nur_musterdaten") is True)
        t("echte_daten_erlaubt == false", cfg.get("echte_daten_erlaubt") is False)

        # 4. Sanierungsmatrix
        matrix = cfg.get("sanierungsmatrix", {})
        t("sanierungsmatrix vorhanden", bool(matrix))

        verantwortlichkeiten = matrix.get("verantwortlichkeiten", [])
        t("Mindestens 5 Verantwortlichkeiten", len(verantwortlichkeiten) >= 5)

        erwartete_v = {"POSTEINGANG", "VORZIMMER", "ANWALT", "AGENT", "SCHLUSSKONTROLLE"}
        tats_v = {v.get("id") for v in verantwortlichkeiten}
        t("Verantwortlichkeiten vollständig", erwartete_v <= tats_v)

        # 5. Sanierungsregeln
        regeln = matrix.get("sanierungsregeln", [])
        t("Genau 9 Sanierungsregeln", len(regeln) == 9)

        erwartete_ids = [f"FEHLER_{i:02d}" for i in range(1, 10)]
        tats_ids = [r.get("fehler_id") for r in regeln]
        t("Regeln decken FEHLER_01..09 ab", tats_ids == erwartete_ids)

        # 6. Jede Regel hat Pflichtfelder
        alle_vollstaendig = all(
            r.get("name") and r.get("schwere") and "automatisch" in r and "bleibt_gesperrt" in r
            for r in regeln
        )
        t("Alle Regeln haben Name+Schwere+automatisch+gesperrt", alle_vollstaendig)

        # 7. Automatische vs manuelle Aktionen konsistent
        konsistent = True
        for r in regeln:
            if r["automatisch"] and not r.get("automatische_aktion"):
                konsistent = False
            if not r["automatisch"] and not r.get("manuelle_aktion"):
                konsistent = False
        t("Automatische/manuelle Aktionen konsistent", konsistent)

        # 8. Ausgabepfade
        ausgabe = cfg.get("ausgabe", {})
        t("html_sanierungsplan definiert", bool(ausgabe.get("html_sanierungsplan")))
        t("json_sanierungsstatus definiert", bool(ausgabe.get("json_sanierungsstatus")))
        t("bericht definiert", bool(ausgabe.get("bericht")))
        t("csv_massnahmen definiert", bool(ausgabe.get("csv_massnahmen")))

        # 9. Sperrregister-Prüfung aktiv
        t("Sperrregister-Prüfung aktiv", cfg.get("register_pruefung", {}).get("sperrregister") is True)

    # 10. Sperrregister
    if os.path.exists(sperrregister_pfad):
        try:
            with open(sperrregister_pfad, "r", encoding="utf-8") as f:
                sperr = json.load(f)
            eintraege = sperr.get("eintraege", [])
            ui08c_eintraege = [e for e in eintraege if e.get("modul_id") == "UI08c"]
            tw("UI08c im Sperrregister eingetragen", len(ui08c_eintraege) > 0)
            if ui08c_eintraege:
                e = ui08c_eintraege[0]
                t("UI08c gesperrt (produktiv)", e.get("gesperrt") is True)
        except Exception as e:
            t("Sperrregister lesbar", False)
            print(f"    -> {e}")
    else:
        tw("Sperrregister existiert", False)

    # 11. Runner-Import
    if os.path.exists(runner_pfad):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("ui08c_runner", runner_pfad)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            t("Runner importierbar", True)
            t("erstelle_sanierungsplan() definiert", hasattr(mod, "erstelle_sanierungsplan"))
            t("generiere_html() definiert", hasattr(mod, "generiere_html"))
            t("generiere_json() definiert", hasattr(mod, "generiere_json"))
            t("generiere_csv() definiert", hasattr(mod, "generiere_csv"))
            t("generiere_bericht() definiert", hasattr(mod, "generiere_bericht"))
            t("hauptlauf() definiert", hasattr(mod, "hauptlauf"))
            t("selbsttest() definiert", hasattr(mod, "selbsttest"))
        except Exception as e:
            t("Runner importierbar", False)
            print(f"    -> {e}")

    # 12. Zusammenfassung
    print("\n" + "=" * 60)
    if FEHLER == 0:
        print(f"CHECK UI08c BESTANDEN – {WARNUNGEN} Warnung(en)")
    else:
        print(f"CHECK UI08c FEHLGESCHLAGEN – {FEHLER} Fehler, {WARNUNGEN} Warnung(en)")
    print("=" * 60)
    return 0 if FEHLER == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
