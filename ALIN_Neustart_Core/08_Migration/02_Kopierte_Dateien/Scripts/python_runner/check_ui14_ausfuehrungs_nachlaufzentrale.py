#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfdatei für UI14 – Ausführungs- und Nachlaufzentrale UI08–UI13
Prüft: Config-Struktur, 8 Schritte, Reihenfolge, Demo-Modus, Freeze-Grenzen,
       Nachlauf, Bericht, Sperrregister-Prüfung
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
    print("UI14 – AUSFUEHRUNGS-NACHLAUFZENTRALE PRÜFDATEI")
    print("=" * 60)

    # 1. Config laden
    cfg_pfad = "Config/ui14_ausfuehrungs_nachlaufzentrale_v1.json"
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

    # 3. 8 Schritte definiert
    schritte = cfg.get("ausfuehrungsreihenfolge", [])
    t("8 Schritte definiert", len(schritte) == 8)

    # 4. Reihenfolge korrekt
    if len(schritte) >= 8:
        t("Schritt 1 = UI08", schritte[0].get("modul_id") == "UI08")
        t("Schritt 2 = UI08b", schritte[1].get("modul_id") == "UI08b")
        t("Schritt 3 = UI08c", schritte[2].get("modul_id") == "UI08c")
        t("Schritt 4 = UI09", schritte[3].get("modul_id") == "UI09")
        t("Schritt 5 = UI10", schritte[4].get("modul_id") == "UI10")
        t("Schritt 6 = UI11", schritte[5].get("modul_id") == "UI11")
        t("Schritt 7 = UI12", schritte[6].get("modul_id") == "UI12")
        t("Schritt 8 = UI13", schritte[7].get("modul_id") == "UI13")

    # 5. Jeder Schritt hat Runner und Check
    for s in schritte:
        t(f"{s['modul_id']} hat runner", bool(s.get("runner")))
        t(f"{s['modul_id']} hat check", bool(s.get("check")))
        t(f"{s['modul_id']} hat abhaengigkeiten", isinstance(s.get("abhaengigkeiten"), list))

    # 6. Demo-Modus
    demo = cfg.get("demo_modus", {})
    t("Demo-Modus: produktiv_freigegeben=false", demo.get("produktiv_freigegeben") is False)
    t("Demo-Modus: nur_musterdaten=true", demo.get("nur_musterdaten") is True)
    t("Demo-Modus: echte_daten_erlaubt=false", demo.get("echte_daten_erlaubt") is False)

    # 7. Sperrregister
    sperr = cfg.get("sperrregister_pruefung", {})
    t("Sperrregister-Prüfung aktiv", sperr.get("aktiv") is True)
    t("Sperrregister: modul_id=UI14", sperr.get("modul_id") == "UI14")

    # 8. Freeze-Grenzen
    freeze = cfg.get("freeze_grenzen", {})
    t("Freeze: beruehrt_ui03_ui07b=false", freeze.get("beruehrt_ui03_ui07b") is False)
    t("Freeze: nur_lesend=true", freeze.get("nur_lesend") is True)
    t("Freeze: neue_dateien=true", freeze.get("neue_dateien") is True)

    # 9. Nachlauf
    nachlauf = cfg.get("nachlauf", {})
    t("Nachlauf HTML definiert", bool(nachlauf.get("html_pfad")))
    t("Nachlauf automatisch_oeffnen", nachlauf.get("automatisch_oeffnen") is True)

    # 10. Bericht
    bericht = cfg.get("bericht", {})
    t("Bericht-Pfad definiert", bool(bericht.get("ausgabe_pfad")))
    t("Zusammenfassung-Pfad definiert", bool(bericht.get("zusammenfassung_pfad")))

    # 11. Fehlerbehandlung
    fb = cfg.get("fehlerbehandlung", {})
    t("Fehlerbehandlung definiert", bool(fb.get("bei_fehler")))
    t("Warnungsbehandlung definiert", bool(fb.get("bei_warnung")))

    # 12. Grenzen
    grenzen = cfg.get("grenzen", {})
    t("max_schritte definiert", grenzen.get("max_schritte", 0) > 0)
    t("timeout definiert", grenzen.get("timeout_pro_schritt_sekunden", 0) > 0)

    # 13. Python-Runner existiert
    t("Python-Runner existiert", os.path.exists("Scripts/python_runner/ui14_ausfuehrungs_nachlaufzentrale.py"))

    # 14. PowerShell-Starter existiert
    t("PowerShell-Starter existiert", os.path.exists("Scripts/UI14_AUSFUEHRUNGS_NACHLAUFZENTRALE_AUTOLAUF.ps1"))

    # 15. Dokumentation existiert
    t("Dokumentation existiert", os.path.exists("Projektplanung/UI14_AUSFUEHRUNGS_NACHLAUFZENTRALE.md"))

    print("\n" + "=" * 60)
    print(f"UI14 Prüfung abgeschlossen. Fehler: {FEHLER}, Warnungen: {WARNUNGEN}")
    print("=" * 60)


if __name__ == "__main__":
    main()
    sys.exit(0 if FEHLER == 0 else 1)
