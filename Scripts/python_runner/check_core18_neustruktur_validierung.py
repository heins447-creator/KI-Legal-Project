#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-18 – Neustruktur Validierung
"""

import os
import sys
import json

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
ERGEBNIS_JSON = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE18_neustruktur_validierung.json")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE18_NEUSTRUKTUR_VALIDIERUNG_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-18 NEUSTRUKTUR =============================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Ergebnis JSON existiert", os.path.exists(ERGEBNIS_JSON))
    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(ERGEBNIS_JSON):
        with open(ERGEBNIS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        t("JSON hat meta", "meta" in data)
        t("JSON hat modul_id CORE-18", data.get("meta", {}).get("modul_id") == "CORE-18")
        t("JSON hat zusammenfassung", "zusammenfassung" in data)
        t("nur_pruefend = true", data.get("meta", {}).get("nur_pruefend") is True)
        t("produktiv_freigegeben = false", data.get("meta", {}).get("produktiv_freigegeben") is False)

        summe = data.get("zusammenfassung", {})
        t("Hat geprueft", "geprueft" in summe)
        t("Hat ok", "ok" in summe)
        t("Hat fehlend", "fehlend" in summe)
        t("Hat validierung_bestanden", "validierung_bestanden" in summe)

        befund = data.get("befund", {})
        t("Befund hat kritisch", "kritisch" in befund)
        t("Befund hat warnung", "warnung" in befund)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
