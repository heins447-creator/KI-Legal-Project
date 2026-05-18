#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-19 – Reste-/Archiv-/Sperrplan
"""

import os
import sys
import json

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
PLAN_JSON = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE19_reste_archiv_sperrplan.json")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE19_RESTE_ARCHIV_SPERRPLAN_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-19 RESTE/ARCHIV/SPERRPLAN ==================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Plan JSON existiert", os.path.exists(PLAN_JSON))
    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(PLAN_JSON):
        with open(PLAN_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        t("JSON hat meta", "meta" in data)
        t("JSON hat modul_id CORE-19", data.get("meta", {}).get("modul_id") == "CORE-19")
        t("JSON hat plaene", "plaene" in data)
        t("nur_planend = true", data.get("meta", {}).get("nur_planend") is True)
        t("produktiv_freigegeben = false", data.get("meta", {}).get("produktiv_freigegeben") is False)

        plaene = data.get("plaene", {})
        t("Plaene hat reste", "reste" in plaene)
        t("Plaene hat archiv", "archiv" in plaene)
        t("Plaene hat gesperrt", "gesperrt" in plaene)
        t("Plaene hat dubletten", "dubletten" in plaene)
        t("Plaene hat manuell", "manuell" in plaene)

        summe = data.get("zusammenfassung", {})
        t("Zusammenfassung hat Eintraege", len(summe) > 0)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
