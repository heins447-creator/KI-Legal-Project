#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-14 – Auswertung der CORE-13 Altbestand-Inventur
"""

import os
import sys
import json
import csv

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
AUSWERTUNG_JSON = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE14_auswertung.json")
AUSWERTUNG_CSV = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE14_auswertung.csv")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE14_AUSWERTUNG_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-14 AUSWERTUNG ==============================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Auswertung JSON existiert", os.path.exists(AUSWERTUNG_JSON))
    t("Auswertung CSV existiert", os.path.exists(AUSWERTUNG_CSV))
    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(AUSWERTUNG_JSON):
        with open(AUSWERTUNG_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        t("JSON hat meta", "meta" in data)
        t("JSON hat modul_id CORE-14", data.get("meta", {}).get("modul_id") == "CORE-14")
        t("JSON hat zusammenfassung", "zusammenfassung" in data)
        t("JSON hat auswertungen", "auswertungen" in data)
        t("produktiv_freigegeben = false", data.get("meta", {}).get("produktiv_freigegeben") is False)
        t("nur_lesend = true", data.get("meta", {}).get("nur_lesend") is True)

        auswertungen = data.get("auswertungen", [])
        if auswertungen:
            first = auswertungen[0]
            t("Eintrag hat relativer_pfad", "relativer_pfad" in first)
            t("Eintrag hat zielentscheidung", "zielentscheidung" in first)
            t("Eintrag hat begruendung", "begruendung" in first)
            t("Eintrag hat gesperrt", "gesperrt" in first)

            ziele = set(a.get("zielentscheidung", "") for a in auswertungen)
            gueltige_ziele = {
                "UEBERNEHMEN_KOPIEREND", "NICHT_UEBERNEHMEN_ERSETZT",
                "ARCHIV_VORSCHLAG", "DUBLETTE_NICHT_KOPIEREN",
                "TESTREST_NICHT_KOPIEREN", "LAUFZEITARTEFAKT_NICHT_KOPIEREN",
                "CONFIG_LOKAL_MANUELL", "SPERREN_NICHT_KOPIEREN",
                "MANUELL_PRUEFEN",
            }
            t("Alle Zielentscheidungen gueltig", ziele.issubset(gueltige_ziele))

            stat = data.get("zusammenfassung", {}).get("zielentscheidungen", {})
            summe = sum(stat.values())
            t("Statistik summiert korrekt", summe == len(auswertungen))

    if os.path.exists(AUSWERTUNG_CSV):
        with open(AUSWERTUNG_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        t("CSV hat Eintraege", len(rows) > 0)
        if rows:
            t("CSV hat zielentscheidung-Spalte", "zielentscheidung" in rows[0])
            t("CSV hat gesperrt-Spalte", "gesperrt" in rows[0])

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
