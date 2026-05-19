#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Datei fuer CORE-20 – Master-Umbau-Bericht
"""

import os
import sys

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE20_MASTER_UMBAU_BERICHT.txt")


def t(bez, bed):
    global FEHLER
    if not bed:
        print(f"  [FAIL] {bez}")
        FEHLER += 1
    else:
        print(f"  [OK]   {bez}")


def main():
    print("CHECK CORE-20 MASTER-UMBAU-BERICHT ====================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    t("Bericht existiert", os.path.exists(BERICHT_PFAD))

    if os.path.exists(BERICHT_PFAD):
        with open(BERICHT_PFAD, "r", encoding="utf-8") as f:
            inhalt = f.read()
        t("Bericht enthaelt CORE-14", "CORE-14 AUSWERTUNG" in inhalt)
        t("Bericht enthaelt CORE-15", "CORE-15 MIGRATIONSPLAN" in inhalt)
        t("Bericht enthaelt CORE-16", "CORE-16 DRY-RUN VALIDIERUNG" in inhalt)
        t("Bericht enthaelt CORE-17", "CORE-17 KOPIERENDE MIGRATION" in inhalt)
        t("Bericht enthaelt CORE-18", "CORE-18 NEUSTRUKTUR VALIDIERUNG" in inhalt)
        t("Bericht enthaelt CORE-19", "CORE-19 RESTE-/ARCHIV-/SPERRPLAN" in inhalt)
        t("Bericht enthaelt Gesamtstatus", "Gesamtstatus:" in inhalt)
        t("Bericht enthaelt Bestaetigungen", "BESTAETIGUNGEN" in inhalt)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
