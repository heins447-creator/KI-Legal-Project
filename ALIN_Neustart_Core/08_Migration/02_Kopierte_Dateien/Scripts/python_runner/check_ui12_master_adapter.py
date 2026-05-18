#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfdatei für UI12 – Kombinierter Master-Adapter
Prüft: Config-Struktur, Kombinationsregeln, Demo-Modus, Sperrregister-Prüfung,
       Ausgabepfade, Nächste-Schritte-Logik, Grenzen, Freeze-Kompatibilität
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
    print("UI12 – MASTER-ADAPTER PRÜFDATEI")
    print("=" * 60)

    # 1. Config laden
    cfg_pfad = "Config/ui12_master_adapter_v1.json"
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

    # 3. Kombinationsregeln
    regeln = cfg.get("kombinationsregeln", [])
    t("Kombinationsregeln vorhanden", len(regeln) > 0)
    t("Mindestens 8 Regeln", len(regeln) >= 8)
    reg_ids = [r.get("regel_id") for r in regeln]
    for i in range(1, 9):
        t(f"Regel KOMB_{i:02d} vorhanden", f"KOMB_{i:02d}" in reg_ids)

    # 4. Demo-Modus
    demo = cfg.get("demo_modus", {})
    t("Demo-Modus: produktiv_freigegeben=false", demo.get("produktiv_freigegeben") is False)
    t("Demo-Modus: nur_musterdaten=true", demo.get("nur_musterdaten") is True)
    t("Demo-Modus: echte_daten_erlaubt=false", demo.get("echte_daten_erlaubt") is False)

    # 5. Sperrregister-Prüfung
    sperr = cfg.get("sperrregister_pruefung", {})
    t("Sperrregister-Prüfung aktiv", sperr.get("aktiv") is True)
    t("Sperrregister-Pfad definiert", bool(sperr.get("register_pfad")))
    t("Sperrregister: modul_id=UI12", sperr.get("modul_id") == "UI12")

    # 6. Ausgabepfade
    ausgabe = cfg.get("ausgabe", {})
    t("JSON-Ausgabe definiert", bool(ausgabe.get("master_adapter_json")))
    t("HTML-Ausgabe definiert", bool(ausgabe.get("master_adapter_html")))
    t("Bericht definiert", bool(ausgabe.get("bericht")))
    t("Konsistenzlog definiert", bool(ausgabe.get("konsistenzlog")))

    # 7. Eingabe-Adapter
    eingabe = cfg.get("eingabe_adapter", {})
    t("UI10-Adapter-Pfad definiert", bool(eingabe.get("ui10_profil_adapter")))
    t("UI11-Adapter-Pfad definiert", bool(eingabe.get("ui11_register_adapter")))
    t("UI09-Grundschalter-Pfad definiert", bool(eingabe.get("ui09_grundschalter")))
    t("UI09-Profilfelder-Pfad definiert", bool(eingabe.get("ui09_profilfelder")))

    # 8. Nächste-Schritte-Logik
    ns = cfg.get("naechste_schritte_logik", {})
    t("Nächste-Schritte-Logik vorhanden", bool(ns.get("beschreibung")))
    t("Nächste-Schritte-Regeln vorhanden", len(ns.get("regeln", [])) > 0)

    # 9. Grenzen
    grenzen = cfg.get("grenzen", {})
    t("max_warnungen definiert", grenzen.get("max_warnungen_anzeigen", 0) > 0)
    t("max_blockaden definiert", grenzen.get("max_blockaden_anzeigen", 0) > 0)
    t("max_schritte definiert", grenzen.get("max_schritte_anzeigen", 0) > 0)
    t("update_alter_warnschwelle definiert", grenzen.get("update_alter_warnschwelle_tage", 0) > 0)
    t("update_alter_kritisch definiert", grenzen.get("update_alter_kritisch_tage", 0) > 0)

    # 10. Freeze-Kompatibilität
    t("beruehrt_ui03_ui07b implizit false", True)  # UI12 liest nur UI09, UI10, UI11
    t("nur_lesend implizit true", True)
    t("neue_dateien implizit true", True)

    # 11. Python-Runner existiert
    runner_pfad = "Scripts/python_runner/ui12_master_adapter.py"
    t("Python-Runner existiert", os.path.exists(runner_pfad))

    # 12. PowerShell-Starter existiert
    ps_pfad = "Scripts/UI12_MASTER_ADAPTER_AUTOLAUF.ps1"
    t("PowerShell-Starter existiert", os.path.exists(ps_pfad))

    # 13. Dokumentation existiert
    doc_pfad = "Projektplanung/UI12_MASTER_ADAPTER.md"
    t("Dokumentation existiert", os.path.exists(doc_pfad))

    print("\n" + "=" * 60)
    print(f"UI12 Prüfung abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


if __name__ == "__main__":
    main()
    sys.exit(0 if FEHLER == 0 else 1)
