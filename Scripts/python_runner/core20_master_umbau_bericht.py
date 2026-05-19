#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-20 – Master-Umbau-Bericht
Erstellt den Gesamtbericht fuer den Umbau-Automanager CORE-14 bis CORE-20.
Nur lesend. Keine Dateien werden kopiert, verschoben, geloescht oder umbenannt.
"""

import json
import os
import sys
from datetime import datetime

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE20_MASTER_UMBAU_BERICHT.txt")

DATEIEN = {
    "CORE14": os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE14_auswertung.json"),
    "CORE15": os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE15_migrationsplan.json"),
    "CORE16": os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE16_dry_run_ergebnis.json"),
    "CORE17": os.path.join(ALIN_CORE, "08_Migration", "09_Manifest", "CORE17_kopierte_dateien_manifest.json"),
    "CORE18": os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE18_neustruktur_validierung.json"),
    "CORE19": os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE19_reste_archiv_sperrplan.json"),
}


def log(msg):
    print(f"[CORE-20] {msg}")


def lade_json(pfad):
    if not os.path.exists(pfad):
        return None
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def erstelle_master_bericht():
    ergebnisse = {}
    for modul, pfad in DATEIEN.items():
        data = lade_json(pfad)
        if data:
            ergebnisse[modul] = data.get("zusammenfassung", {})
            ergebnisse[modul]["_status"] = "OK"
        else:
            ergebnisse[modul] = {"_status": "NICHT_GEFUNDEN"}

    # Bestimme Gesamtstatus
    core16_frei = ergebnisse.get("CORE16", {}).get("dry_run_freigegeben", False)
    core17_status = ergebnisse.get("CORE17", {}).get("_status", "NICHT_GEFUNDEN")
    core17_blockiert = False
    if core17_status == "OK":
        meta = lade_json(DATEIEN["CORE17"])
        if meta and meta.get("meta", {}).get("status") == "BLOCKIERT":
            core17_blockiert = True

    core18_bestanden = ergebnisse.get("CORE18", {}).get("validierung_bestanden", False)

    gesamtstatus = "OK"
    if not core16_frei:
        gesamtstatus = "BLOCKIERT (Dry-Run nicht freigegeben)"
    elif core17_blockiert:
        gesamtstatus = "BLOCKIERT (CORE-17 blockiert)"
    elif not core18_bestanden and core17_status == "OK":
        gesamtstatus = "WARNUNG (Validierung nicht bestanden)"

    return ergebnisse, gesamtstatus


def schreibe_bericht(ergebnisse, gesamtstatus):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-20 MASTER-UMBAU-BERICHT\n")
        f.write("Autonomer Umbau-Automanager CORE-14 bis CORE-20\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        f.write(f"Gesamtstatus: {gesamtstatus}\n\n")

        # CORE-14
        f.write("CORE-14 AUSWERTUNG\n")
        f.write("-" * 40 + "\n")
        e14 = ergebnisse.get("CORE14", {})
        if e14.get("_status") == "OK":
            f.write(f"  Gesamtdateien: {e14.get('anzahl_dateien', 0)}\n")
            f.write(f"  Gesperrt: {e14.get('anzahl_gesperrt', 0)}\n")
            ziele = e14.get("zielentscheidungen", {})
            for ziel, anzahl in sorted(ziele.items()):
                f.write(f"  {ziel:<45} {anzahl:>6}\n")
        else:
            f.write(f"  Status: {e14.get('_status', 'UNBEKANNT')}\n")
        f.write("\n")

        # CORE-15
        f.write("CORE-15 MIGRATIONSPLAN\n")
        f.write("-" * 40 + "\n")
        e15 = ergebnisse.get("CORE15", {})
        if e15.get("_status") == "OK":
            f.write(f"  Gesamtdateien: {e15.get('anzahl_dateien', 0)}\n")
            f.write(f"  Konflikte: {e15.get('anzahl_konflikte', 0)}\n")
            f.write(f"  Kopierende: {e15.get('kopierende_dateien', 0)}\n")
        else:
            f.write(f"  Status: {e15.get('_status', 'UNBEKANNT')}\n")
        f.write("\n")

        # CORE-16
        f.write("CORE-16 DRY-RUN VALIDIERUNG\n")
        f.write("-" * 40 + "\n")
        e16 = ergebnisse.get("CORE16", {})
        if e16.get("_status") == "OK":
            f.write(f"  Geprueft: {e16.get('geprueft', 0)}\n")
            f.write(f"  OK: {e16.get('ok', 0)}\n")
            f.write(f"  Warnungen: {e16.get('warnung', 0)}\n")
            f.write(f"  Kritisch: {e16.get('kritisch', 0)}\n")
            f.write(f"  Freigegeben: {e16.get('dry_run_freigegeben', False)}\n")
        else:
            f.write(f"  Status: {e16.get('_status', 'UNBEKANNT')}\n")
        f.write("\n")

        # CORE-17
        f.write("CORE-17 KOPIERENDE MIGRATION\n")
        f.write("-" * 40 + "\n")
        e17 = ergebnisse.get("CORE17", {})
        if e17.get("_status") == "OK":
            meta = lade_json(DATEIEN["CORE17"])
            if meta and meta.get("meta", {}).get("status") == "BLOCKIERT":
                f.write(f"  Status: BLOCKIERT\n")
                f.write(f"  Grund: {meta.get('meta', {}).get('grund', 'Unbekannt')}\n")
            else:
                f.write(f"  Geplant: {e17.get('geplant', 0)}\n")
                f.write(f"  Kopiert: {e17.get('kopiert', 0)}\n")
                f.write(f"  Uebersprungen (gesperrt): {e17.get('uebersprungen_gesperrt', 0)}\n")
                f.write(f"  Fehler: {e17.get('fehler', 0)}\n")
                f.write(f"  Bytes kopiert: {e17.get('bytes_kopiert', 0)}\n")
        else:
            f.write(f"  Status: {e17.get('_status', 'UNBEKANNT')}\n")
        f.write("\n")

        # CORE-18
        f.write("CORE-18 NEUSTRUKTUR VALIDIERUNG\n")
        f.write("-" * 40 + "\n")
        e18 = ergebnisse.get("CORE18", {})
        if e18.get("_status") == "OK":
            f.write(f"  Geprueft: {e18.get('geprueft', 0)}\n")
            f.write(f"  OK: {e18.get('ok', 0)}\n")
            f.write(f"  Fehlend: {e18.get('fehlend', 0)}\n")
            f.write(f"  Groesse abweichend: {e18.get('groesse_abweichend', 0)}\n")
            f.write(f"  SHA abweichend: {e18.get('sha_abweichend', 0)}\n")
            f.write(f"  Bestanden: {e18.get('validierung_bestanden', False)}\n")
        else:
            f.write(f"  Status: {e18.get('_status', 'UNBEKANNT')}\n")
        f.write("\n")

        # CORE-19
        f.write("CORE-19 RESTE-/ARCHIV-/SPERRPLAN\n")
        f.write("-" * 40 + "\n")
        e19 = ergebnisse.get("CORE19", {})
        if e19.get("_status") == "OK":
            for kategorie, anzahl in sorted(e19.items()):
                if not kategorie.startswith("_"):
                    f.write(f"  {kategorie:<30} {anzahl:>6}\n")
        else:
            f.write(f"  Status: {e19.get('_status', 'UNBEKANNT')}\n")
        f.write("\n")

        # Bestaetigungen
        f.write("BESTAETIGUNGEN\n")
        f.write("-" * 40 + "\n")
        f.write("  [ ] Keine alten Dateien wurden geloescht\n")
        f.write("  [ ] Keine alten Dateien wurden verschoben\n")
        f.write("  [ ] Keine alten Dateien wurden umbenannt\n")
        f.write("  [ ] Nur kopierende Operationen durchgefuehrt\n")
        f.write("  [ ] UI03–UI07b wurden nicht geaendert\n")
        f.write("  [ ] Keine Produktivfreigabe behauptet\n")
        f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("ENDE MASTER-UMBAU-BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def hauptlauf():
    log("Starte CORE-20 Master-Umbau-Bericht...")

    log("Sammle Ergebnisse...")
    ergebnisse, gesamtstatus = erstelle_master_bericht()

    schreibe_bericht(ergebnisse, gesamtstatus)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Gesamtstatus: {gesamtstatus}")
    for modul, data in ergebnisse.items():
        status = data.get("_status", "UNBEKANNT")
        log(f"  {modul}: {status}")
    log("=" * 60)
    log("CORE-20 MASTER-UMBAU-BERICHT ABGESCHLOSSEN")


def selbsttest():
    print("CORE-20 SELBSTTEST =====================================")
    global FEHLER, WARNUNGEN
    FEHLER = 0
    WARNUNGEN = 0

    def t(bez, bed):
        global FEHLER
        if not bed:
            print(f"  [FAIL] {bez}")
            FEHLER += 1
        else:
            print(f"  [OK]   {bez}")

    t("Projektwurzel existiert", os.path.isdir(PROJEKT_WURZEL))
    t("ALIN_Neustart_Core existiert", os.path.isdir(ALIN_CORE))
    t("DATEIEN definiert", len(DATEIEN) == 6)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
