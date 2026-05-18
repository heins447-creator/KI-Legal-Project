#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-17 – Kopierende Migration
"""

import os
import sys
import json

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
MANIFEST_PFAD = os.path.join(ALIN_CORE, "08_Migration", "09_Manifest", "CORE17_kopierte_dateien_manifest.json")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE17_KOPIERENDE_MIGRATION_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-17 KOPIERENDE MIGRATION ====================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Manifest existiert", os.path.exists(MANIFEST_PFAD))
    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(MANIFEST_PFAD):
        with open(MANIFEST_PFAD, "r", encoding="utf-8") as f:
            data = json.load(f)
        t("Manifest hat meta", "meta" in data)
        t("Manifest hat modul_id CORE-17", data.get("meta", {}).get("modul_id") == "CORE-17")
        t("Manifest hat kopierte_dateien", "kopierte_dateien" in data)
        t("nur_kopierend = true", data.get("meta", {}).get("nur_kopierend") is True)
        t("produktiv_freigegeben = false", data.get("meta", {}).get("produktiv_freigegeben") is False)

        summe = data.get("zusammenfassung", {})
        t("Hat geplant", "geplant" in summe)
        t("Hat kopiert", "kopiert" in summe)
        t("Hat fehler", "fehler" in summe)

        status = data.get("meta", {}).get("status", "")
        if status == "BLOCKIERT":
            t("Blockade dokumentiert", True)
            t("Blockadegrund vorhanden", bool(data.get("meta", {}).get("grund", "")))
        else:
            kopierte = data.get("kopierte_dateien", [])
            t("Kopierte Dateien ist Liste", isinstance(kopierte, list))
            if kopierte:
                t("Eintrag hat ziel_pfad", "ziel_pfad" in kopierte[0])
                t("Eintrag hat sha256", "sha256" in kopierte[0])

            # Pruefe, dass kopierte Dateien existieren
            for eintrag in kopierte[:10]:
                ziel = eintrag.get("ziel_pfad", "")
                if ziel and os.path.exists(ziel):
                    t(f"Datei existiert: {os.path.basename(ziel)}", True)
                elif ziel:
                    t(f"Datei existiert: {os.path.basename(ziel)}", False)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
