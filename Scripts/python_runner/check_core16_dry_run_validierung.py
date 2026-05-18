#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-16 – Dry-Run Validierung
"""

import os
import sys
import json

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
ERGEBNIS_JSON = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE16_dry_run_ergebnis.json")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE16_DRY_RUN_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-16 DRY-RUN ================================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Ergebnis JSON existiert", os.path.exists(ERGEBNIS_JSON))
    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(ERGEBNIS_JSON):
        with open(ERGEBNIS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        t("JSON hat meta", "meta" in data)
        t("JSON hat modul_id CORE-16", data.get("meta", {}).get("modul_id") == "CORE-16")
        t("JSON hat zusammenfassung", "zusammenfassung" in data)
        t("JSON hat befund", "befund" in data)
        t("nur_pruefend = true", data.get("meta", {}).get("nur_pruefend") is True)
        t("produktiv_freigegeben = false", data.get("meta", {}).get("produktiv_freigegeben") is False)

        summe = data.get("zusammenfassung", {})
        t("Hat geprueft", "geprueft" in summe)
        t("Hat ok", "ok" in summe)
        t("Hat warnung", "warnung" in summe)
        t("Hat kritisch", "kritisch" in summe)
        t("Hat dry_run_freigegeben", "dry_run_freigegeben" in summe)

        befund = data.get("befund", {})
        t("Befund hat kritisch", "kritisch" in befund)
        t("Befund hat warnung", "warnung" in befund)
        t("Befund hat info", "info" in befund)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
