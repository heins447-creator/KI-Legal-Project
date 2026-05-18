#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-15 – Migrationsplan
"""

import os
import sys
import json
import csv

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
PLAN_JSON = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE15_migrationsplan.json")
PLAN_CSV = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE15_migrationsplan.csv")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE15_MIGRATIONSPLAN_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-15 MIGRATIONSPLAN ==========================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Migrationsplan JSON existiert", os.path.exists(PLAN_JSON))
    t("Migrationsplan CSV existiert", os.path.exists(PLAN_CSV))
    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(PLAN_JSON):
        with open(PLAN_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        t("JSON hat meta", "meta" in data)
        t("JSON hat modul_id CORE-15", data.get("meta", {}).get("modul_id") == "CORE-15")
        t("JSON hat plaene", "plaene" in data)
        t("nur_planend = true", data.get("meta", {}).get("nur_planend") is True)
        t("produktiv_freigegeben = false", data.get("meta", {}).get("produktiv_freigegeben") is False)

        plaene = data.get("plaene", [])
        if plaene:
            first = plaene[0]
            t("Plan hat relativer_pfad", "relativer_pfad" in first)
            t("Plan hat ziel_pfad", "ziel_pfad" in first)
            t("Plan hat ziel_ordner", "ziel_ordner" in first)
            t("Plan hat kopieren", "kopieren" in first)

            ziele = set(p.get("ziel_ordner", "") for p in plaene)
            gueltige = {"02_Kopierte_Dateien", "03_Manuell_Pruefen", "04_Gesperrt",
                        "05_Dubletten", "06_Testreste", "07_Laufzeit_Artefakte", "08_Archiv_Vorschlag"}
            t("Alle ziel_ordner gueltig", ziele.issubset(gueltige))

        konflikte = data.get("konflikte", [])
        t("Konflikte ist Liste", isinstance(konflikte, list))

    if os.path.exists(PLAN_CSV):
        with open(PLAN_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        t("CSV hat Eintraege", len(rows) > 0)
        if rows:
            t("CSV hat ziel_pfad-Spalte", "ziel_pfad" in rows[0])
            t("CSV hat kopieren-Spalte", "kopieren" in rows[0])

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
