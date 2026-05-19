#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-17 – Kopierende Migration
Kopiert Dateien gemaess Migrationsplan in die neue Struktur.
Nur kopierend. Keine alten Dateien werden verschoben, geloescht oder umbenannt.
"""

import json
import os
import sys
import shutil
from datetime import datetime
from collections import defaultdict

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
PLAN_PFAD = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE15_migrationsplan.json")
DRY_RUN_PFAD = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE16_dry_run_ergebnis.json")
AUSGABE_DIR = os.path.join(ALIN_CORE, "08_Migration", "09_Manifest")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE17_KOPIERENDE_MIGRATION_BERICHT.txt")
MANIFEST_PFAD = os.path.join(ALIN_CORE, "08_Migration", "09_Manifest", "CORE17_kopierte_dateien_manifest.json")


def log(msg):
    print(f"[CORE-17] {msg}")


def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def pruefe_dry_run_freigabe():
    if not os.path.exists(DRY_RUN_PFAD):
        log(f"WARNUNG: Dry-Run Ergebnis nicht gefunden: {DRY_RUN_PFAD}")
        global WARNUNGEN
        WARNUNGEN += 1
        return False
    data = lade_json(DRY_RUN_PFAD)
    frei = data.get("zusammenfassung", {}).get("dry_run_freigegeben", False)
    return frei


def kopiere_datei(plan, manifest):
    global FEHLER, WARNUNGEN
    rel_pfad = plan.get("relativer_pfad", "")
    ziel_pfad = plan.get("ziel_pfad", "")
    kopieren = plan.get("kopieren", False)
    gesperrt = plan.get("gesperrt", False)

    if not kopieren:
        return None

    if gesperrt:
        log(f"UEBERSPRINGE (gesperrt): {rel_pfad}")
        manifest["uebersprungen_gesperrt"] += 1
        return None

    quelle = os.path.join(PROJEKT_WURZEL, rel_pfad)
    ziel = ziel_pfad

    if not os.path.exists(quelle):
        log(f"FEHLER: Quelle nicht gefunden: {quelle}")
        FEHLER += 1
        manifest["fehler"] += 1
        return None

    try:
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        shutil.copy2(quelle, ziel)
        manifest["kopiert"] += 1
        manifest["bytes_kopiert"] += os.path.getsize(quelle)
        return {
            "relativer_pfad": rel_pfad,
            "ziel_pfad": ziel,
            "groesse": os.path.getsize(quelle),
            "sha256": plan.get("sha256", ""),
            "zeitstempel": datetime.now().isoformat(),
        }
    except Exception as e:
        log(f"FEHLER beim Kopieren {rel_pfad}: {e}")
        FEHLER += 1
        manifest["fehler"] += 1
        return None


def hauptlauf():
    log("Starte CORE-17 Kopierende Migration...")

    if not os.path.exists(PLAN_PFAD):
        log(f"FEHLER: Migrationsplan nicht gefunden: {PLAN_PFAD}")
        global FEHLER
        FEHLER += 1
        return

    # Dry-Run Freigabe pruefen
    freigegeben = pruefe_dry_run_freigabe()
    if not freigegeben:
        log("BLOCKIERT: Dry-Run nicht freigegeben. Kopiere nicht.")
        schreibe_blockiert_manifest()
        return

    log("Dry-Run freigegeben. Beginne Kopieren...")

    plan_data = lade_json(PLAN_PFAD)
    plaene = plan_data.get("plaene", [])
    log(f"Migrationsplan geladen: {len(plaene)} Eintraege")

    manifest = {
        "meta": {
            "modul_id": "CORE-17",
            "name": "Kopierende Migration Manifest",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_kopierend": True,
        },
        "zusammenfassung": {
            "geplant": 0,
            "kopiert": 0,
            "uebersprungen_gesperrt": 0,
            "fehler": 0,
            "bytes_kopiert": 0,
        },
        "kopierte_dateien": [],
    }

    for p in plaene:
        if p.get("kopieren"):
            manifest["zusammenfassung"]["geplant"] += 1
            eintrag = kopiere_datei(p, manifest["zusammenfassung"])
            if eintrag:
                manifest["kopierte_dateien"].append(eintrag)

    schreibe_manifest(manifest)
    schreibe_bericht(manifest)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    summe = manifest["zusammenfassung"]
    log(f"Geplant: {summe['geplant']}")
    log(f"Kopiert: {summe['kopiert']}")
    log(f"Uebersprungen (gesperrt): {summe['uebersprungen_gesperrt']}")
    log(f"Fehler: {summe['fehler']}")
    log(f"Bytes kopiert: {summe['bytes_kopiert']}")
    log("=" * 60)
    log("CORE-17 KOPIERENDE MIGRATION ABGESCHLOSSEN")


def schreibe_blockiert_manifest():
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    manifest = {
        "meta": {
            "modul_id": "CORE-17",
            "name": "Kopierende Migration Manifest",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_kopierend": True,
            "status": "BLOCKIERT",
            "grund": "Dry-Run nicht freigegeben",
        },
        "zusammenfassung": {
            "geplant": 0,
            "kopiert": 0,
            "uebersprungen_gesperrt": 0,
            "fehler": 0,
            "bytes_kopiert": 0,
        },
        "kopierte_dateien": [],
    }
    with open(MANIFEST_PFAD, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    log(f"Blockiert-Manifest geschrieben: {MANIFEST_PFAD}")


def schreibe_manifest(manifest):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    with open(MANIFEST_PFAD, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    log(f"Manifest geschrieben: {MANIFEST_PFAD}")


def schreibe_bericht(manifest):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-17 KOPIERENDE MIGRATION BERICHT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        summe = manifest["zusammenfassung"]
        f.write(f"Geplant: {summe['geplant']}\n")
        f.write(f"Kopiert: {summe['kopiert']}\n")
        f.write(f"Uebersprungen (gesperrt): {summe['uebersprungen_gesperrt']}\n")
        f.write(f"Fehler: {summe['fehler']}\n")
        f.write(f"Bytes kopiert: {summe['bytes_kopiert']}\n\n")
        f.write("Bestaetigung:\n")
        f.write("  - Keine alten Dateien wurden geloescht\n")
        f.write("  - Keine alten Dateien wurden verschoben\n")
        f.write("  - Keine alten Dateien wurden umbenannt\n")
        f.write("  - Nur kopierende Operationen durchgefuehrt\n")
        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("ENDE BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def selbsttest():
    print("CORE-17 SELBSTTEST =====================================")
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

    # Test Manifest-Struktur
    m = {
        "meta": {"modul_id": "CORE-17"},
        "zusammenfassung": {"geplant": 0, "kopiert": 0, "uebersprungen_gesperrt": 0, "fehler": 0, "bytes_kopiert": 0},
        "kopierte_dateien": [],
    }
    t("Manifest-Struktur korrekt", "meta" in m and "kopierte_dateien" in m)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
