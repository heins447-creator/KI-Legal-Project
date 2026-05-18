#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-18 – Validierung der neuen Struktur
Prueft, ob alle kopierten Dateien im Ziel korrekt angekommen sind.
Nur pruefend. Keine Dateien werden kopiert, verschoben, geloescht oder umbenannt.
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

FEHLER = 0
WARNUNGEN = 0

PROJEKT_WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALIN_CORE = os.path.join(PROJEKT_WURZEL, "ALIN_Neustart_Core")
MANIFEST_PFAD = os.path.join(ALIN_CORE, "08_Migration", "09_Manifest", "CORE17_kopierte_dateien_manifest.json")
AUSGABE_DIR = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE18_NEUSTRUKTUR_VALIDIERUNG_BERICHT.txt")


def log(msg):
    print(f"[CORE-18] {msg}")


def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def validiere_neustruktur(manifest):
    kopierte = manifest.get("kopierte_dateien", [])
    befund = {
        "kritisch": [],
        "warnung": [],
        "info": [],
    }
    statistik = {
        "geprueft": 0,
        "ok": 0,
        "fehlend": 0,
        "groesse_abweichend": 0,
        "sha_abweichend": 0,
    }

    for eintrag in kopierte:
        statistik["geprueft"] += 1
        ziel_pfad = eintrag.get("ziel_pfad", "")
        erwartete_groesse = eintrag.get("groesse", 0)
        erwarteter_sha = eintrag.get("sha256", "")

        if not os.path.exists(ziel_pfad):
            befund["kritisch"].append({
                "pfad": ziel_pfad,
                "grund": "Datei fehlt im Ziel",
            })
            statistik["fehlend"] += 1
            continue

        tatsaechliche_groesse = os.path.getsize(ziel_pfad)
        if tatsaechliche_groesse != erwartete_groesse:
            befund["warnung"].append({
                "pfad": ziel_pfad,
                "grund": f"Groesse abweichend: erwartet {erwartete_groesse}, ist {tatsaechliche_groesse}",
            })
            statistik["groesse_abweichend"] += 1

        # SHA-Pruefung (optional, da teuer)
        if erwarteter_sha:
            import hashlib
            h = hashlib.sha256()
            with open(ziel_pfad, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            tatsaechlicher_sha = h.hexdigest()
            if tatsaechlicher_sha != erwarteter_sha:
                befund["kritisch"].append({
                    "pfad": ziel_pfad,
                    "grund": f"SHA256 abweichend",
                })
                statistik["sha_abweichend"] += 1

        statistik["ok"] += 1

    return befund, statistik


def schreibe_json(befund, statistik):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE18_neustruktur_validierung.json")
    out = {
        "meta": {
            "modul_id": "CORE-18",
            "name": "Validierung der neuen Struktur",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_pruefend": True,
        },
        "zusammenfassung": {
            "geprueft": statistik["geprueft"],
            "ok": statistik["ok"],
            "fehlend": statistik["fehlend"],
            "groesse_abweichend": statistik["groesse_abweichend"],
            "sha_abweichend": statistik["sha_abweichend"],
            "validierung_bestanden": statistik["fehlend"] == 0 and statistik["sha_abweichend"] == 0,
        },
        "befund": befund,
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"JSON geschrieben: {pfad}")
    return pfad


def schreibe_bericht(befund, statistik):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-18 NEUSTRUKTUR VALIDIERUNG BERICHT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        f.write(f"Geprueft: {statistik['geprueft']}\n")
        f.write(f"OK: {statistik['ok']}\n")
        f.write(f"Fehlend: {statistik['fehlend']}\n")
        f.write(f"Groesse abweichend: {statistik['groesse_abweichend']}\n")
        f.write(f"SHA abweichend: {statistik['sha_abweichend']}\n")
        bestanden = statistik["fehlend"] == 0 and statistik["sha_abweichend"] == 0
        f.write(f"Validierung BESTANDEN: {bestanden}\n\n")

        if befund["kritisch"]:
            f.write("KRITISCHE BEFUNDE:\n")
            f.write("-" * 40 + "\n")
            for b in befund["kritisch"][:30]:
                f.write(f"  [KRITISCH] {b['pfad']}\n")
                f.write(f"             {b['grund']}\n")
            if len(befund["kritisch"]) > 30:
                f.write(f"  ... und {len(befund['kritisch']) - 30} weitere\n")
            f.write("\n")

        if befund["warnung"]:
            f.write("WARNUNGEN:\n")
            f.write("-" * 40 + "\n")
            for b in befund["warnung"][:20]:
                f.write(f"  [WARNUNG] {b['pfad']}\n")
                f.write(f"            {b['grund']}\n")
            if len(befund["warnung"]) > 20:
                f.write(f"  ... und {len(befund['warnung']) - 20} weitere\n")
            f.write("\n")

        if bestanden:
            f.write("Alle geprueften Dateien sind korrekt im Ziel angekommen.\n\n")

        f.write("=" * 70 + "\n")
        f.write("ENDE BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def hauptlauf():
    log("Starte CORE-18 Neustruktur Validierung...")

    if not os.path.exists(MANIFEST_PFAD):
        log(f"FEHLER: Manifest nicht gefunden: {MANIFEST_PFAD}")
        global FEHLER
        FEHLER += 1
        return

    log(f"Lade Manifest: {MANIFEST_PFAD}")
    manifest = lade_json(MANIFEST_PFAD)
    kopierte = manifest.get("kopierte_dateien", [])
    log(f"Manifest geladen: {len(kopierte)} kopierte Dateien")

    # Pruefe auf Blockade
    status = manifest.get("meta", {}).get("status", "")
    if status == "BLOCKIERT":
        log("CORE-17 war blockiert. Keine Dateien zu validieren.")
        schreibe_leeres_ergebnis()
        return

    log("Validiere Neustruktur...")
    befund, statistik = validiere_neustruktur(manifest)

    schreibe_json(befund, statistik)
    schreibe_bericht(befund, statistik)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Geprueft: {statistik['geprueft']}")
    log(f"OK: {statistik['ok']}")
    log(f"Fehlend: {statistik['fehlend']}")
    log(f"Groesse abweichend: {statistik['groesse_abweichend']}")
    log(f"SHA abweichend: {statistik['sha_abweichend']}")
    bestanden = statistik["fehlend"] == 0 and statistik["sha_abweichend"] == 0
    log(f"Validierung BESTANDEN: {bestanden}")
    log("=" * 60)
    log("CORE-18 NEUSTRUKTUR VALIDIERUNG ABGESCHLOSSEN")


def schreibe_leeres_ergebnis():
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE18_neustruktur_validierung.json")
    out = {
        "meta": {
            "modul_id": "CORE-18",
            "name": "Validierung der neuen Struktur",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_pruefend": True,
            "status": "BLOCKIERT",
            "grund": "CORE-17 war blockiert",
        },
        "zusammenfassung": {
            "geprueft": 0,
            "ok": 0,
            "fehlend": 0,
            "groesse_abweichend": 0,
            "sha_abweichend": 0,
            "validierung_bestanden": False,
        },
        "befund": {"kritisch": [], "warnung": [], "info": []},
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"Leeres Ergebnis geschrieben: {pfad}")


def selbsttest():
    print("CORE-18 SELBSTTEST =====================================")
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

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
