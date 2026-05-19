#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfdatei für UI13 – Abnahme- und Entscheidungsübersicht UI08–UI12
Prüft: Config-Struktur, Module UI08–UI12, Demo-Modus, Freeze-Grenzen,
       Ausgabepfade, Entscheidungslogik, Sperrregister-Prüfung
"""

import json
import os
import sys

FEHLER = 0
WARNUNGEN = 0


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"[PRÜFUNG FEHLER] {bez}")
        FEHLER += 1
    else:
        print(f"[PRÜFUNG OK] {bez}")


def main():
    global FEHLER, WARNUNGEN
    print("=" * 60)
    print("UI13 – ABNAHME-ENTSCHEIDUNGSUEBERSICHT PRÜFDATEI")
    print("=" * 60)

    # 1. Config laden
    cfg_pfad = "Config/ui13_abnahme_entscheidungsuebersicht_v1.json"
    if not os.path.exists(cfg_pfad):
        print(f"[FEHLER] Config nicht gefunden: {cfg_pfad}")
        FEHLER += 1
        return
    with open(cfg_pfad, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # 2. Pflichtfelder
    t("modul_id vorhanden", bool(cfg.get("modul_id")))
    t("name vorhanden", bool(cfg.get("name")))
    t("version vorhanden", bool(cfg.get("version")))
    t("beschreibung vorhanden", bool(cfg.get("beschreibung")))

    # 3. Module UI08–UI12
    module = cfg.get("module", [])
    t("Mindestens 7 Module (UI08–UI12)", len(module) >= 7)
    mod_ids = [m.get("modul_id") for m in module]
    for expected in ["UI08", "UI08b", "UI08c", "UI09", "UI10", "UI11", "UI12"]:
        t(f"Modul {expected} definiert", expected in mod_ids)

    # 4. Commit-Hashes vorhanden
    for m in module:
        t(f"{m['modul_id']} hat Commit-Hash", bool(m.get("commit_hash")))

    # 5. Ausgabepfade pro Modul
    for m in module:
        t(f"{m['modul_id']} hat Ausgaben definiert",
          bool(m.get("ausgabe_json") or m.get("ausgabe_html") or m.get("ausgabe_txt")))

    # 6. Demo-Modus
    demo = cfg.get("demo_modus", {})
    t("Demo-Modus: produktiv_freigegeben=false", demo.get("produktiv_freigegeben") is False)
    t("Demo-Modus: nur_musterdaten=true", demo.get("nur_musterdaten") is True)
    t("Demo-Modus: echte_daten_erlaubt=false", demo.get("echte_daten_erlaubt") is False)

    # 7. Sperrregister
    sperr = cfg.get("sperrregister_pruefung", {})
    t("Sperrregister-Prüfung aktiv", sperr.get("aktiv") is True)
    t("Sperrregister: modul_id=UI13", sperr.get("modul_id") == "UI13")

    # 8. Freeze-Grenzen
    freeze = cfg.get("freeze_grenzen", {})
    t("Freeze: beruehrt_ui03_ui07b=false", freeze.get("beruehrt_ui03_ui07b") is False)
    t("Freeze: nur_lesend=true", freeze.get("nur_lesend") is True)
    t("Freeze: neue_dateien=true", freeze.get("neue_dateien") is True)
    t("Freeze: erlaubte_lesepfade vorhanden", len(freeze.get("erlaubte_lesepfade", [])) > 0)

    # 9. Ausgabepfade UI13
    ausgabe = cfg.get("ausgabe", {})
    t("HTML-Ausgabe definiert", bool(ausgabe.get("uebersicht_html")))
    t("JSON-Ausgabe definiert", bool(ausgabe.get("uebersicht_json")))
    t("Bericht definiert", bool(ausgabe.get("bericht")))

    # 10. Entscheidungslogik
    regeln = cfg.get("naechste_schritte_logik", {}).get("regeln", [])
    t("Entscheidungsregeln vorhanden", len(regeln) > 0)
    t("Regel: alle_abgeschlossen", any("alle_module_abgeschlossen" in r.get("bedingung", "") for r in regeln))
    t("Regel: adapter_fehlt", any("adapter_fehlt" in r.get("bedingung", "") for r in regeln))
    t("Regel: blockaden", any("kritische_blockaden" in r.get("bedingung", "") for r in regeln))

    # 11. Grenzen
    grenzen = cfg.get("grenzen", {})
    t("max_module definiert", grenzen.get("max_module_anzeigen", 0) > 0)
    t("max_warnungen definiert", grenzen.get("max_warnungen_anzeigen", 0) > 0)

    # 12. Python-Runner existiert
    t("Python-Runner existiert", os.path.exists("Scripts/python_runner/ui13_abnahme_entscheidungsuebersicht.py"))

    # 13. PowerShell-Starter existiert
    t("PowerShell-Starter existiert", os.path.exists("Scripts/UI13_ABNAHME_ENTSCHEIDUNGSUEBERSICHT_AUTOLAUF.ps1"))

    # 14. Dokumentation existiert
    t("Dokumentation existiert", os.path.exists("Projektplanung/UI13_ABNAHME_ENTSCHEIDUNGSUEBERSICHT.md"))

    print("\n" + "=" * 60)
    print(f"UI13 Prüfung abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


if __name__ == "__main__":
    main()
    sys.exit(0 if FEHLER == 0 else 1)
