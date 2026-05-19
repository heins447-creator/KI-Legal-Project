#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-16 – Dry-Run Validierung des Migrationsplans
Prueft den Migrationsplan auf Kollisionen, Pfade, SHA-Konsistenz und Sperrstatus.
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
PLAN_PFAD = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene", "CORE15_migrationsplan.json")
AUSGABE_DIR = os.path.join(ALIN_CORE, "08_Migration", "01_Plaene")
BERICHT_PFAD = os.path.join(ALIN_CORE, "Reports", "CORE16_DRY_RUN_BERICHT.txt")


def log(msg):
    print(f"[CORE-16] {msg}")


def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def validiere_plan(plan_data):
    plaene = plan_data.get("plaene", [])
    konflikte = plan_data.get("konflikte", [])

    befund = {
        "kritisch": [],
        "warnung": [],
        "info": [],
    }
    statistik = {
        "geprueft": 0,
        "ok": 0,
        "warnung": 0,
        "kritisch": 0,
        "gesperrt": 0,
        "kopieren_vorgesehen": 0,
    }

    zielpfade = defaultdict(list)
    sha_zu_quelle = defaultdict(list)

    for p in plaene:
        statistik["geprueft"] += 1
        rel_pfad = p.get("relativer_pfad", "")
        ziel_pfad = p.get("ziel_pfad", "")
        ziel = p.get("zielentscheidung", "")
        sha = p.get("sha256", "")
        gesperrt = p.get("gesperrt", False)
        kopieren = p.get("kopieren", False)

        # Zielpfad-Kollisionen
        zielpfade[ziel_pfad].append(rel_pfad)

        # SHA-Konsistenz
        if sha:
            sha_zu_quelle[sha].append(rel_pfad)

        # Sperrpruefung
        if gesperrt and kopieren:
            befund["kritisch"].append({
                "pfad": rel_pfad,
                "grund": "Gesperrte Datei soll kopiert werden",
            })
            statistik["kritisch"] += 1

        if kopieren:
            statistik["kopieren_vorgesehen"] += 1

        # Quelldatei existiert pruefen
        quelle_abs = os.path.join(PROJEKT_WURZEL, rel_pfad)
        if not os.path.exists(quelle_abs):
            befund["warnung"].append({
                "pfad": rel_pfad,
                "grund": "Quelldatei nicht gefunden",
            })
            statistik["warnung"] += 1

    # Zielpfad-Kollisionen auswerten
    for ziel_pfad, quellen in zielpfade.items():
        if len(quellen) > 1:
            befund["kritisch"].append({
                "pfad": ziel_pfad,
                "grund": f"Zielpfad-Kollision: {len(quellen)} Quellen",
                "quellen": quellen,
            })
            statistik["kritisch"] += 1

    # SHA-Dubletten im Kopierplan
    for sha, quellen in sha_zu_quelle.items():
        if len(quellen) > 1:
            # Nur wenn mindestens eine kopiert werden soll
            kopierende = [q for q in quellen if any(
                p.get("relativer_pfad") == q and p.get("kopieren") for p in plaene
            )]
            if len(kopierende) > 1:
                befund["warnung"].append({
                    "pfad": sha[:16] + "...",
                    "grund": f"SHA-Dublette im Kopierplan: {len(kopierende)} Dateien",
                    "quellen": kopierende,
                })
                statistik["warnung"] += 1

    # Bestehende Konflikte aus CORE-15
    for k in konflikte:
        befund["kritisch"].append({
            "pfad": k.get("relativer_pfad", ""),
            "grund": f"Bekannter Konflikt: {k.get('grund', '')}",
        })
        statistik["kritisch"] += 1

    statistik["ok"] = statistik["geprueft"] - statistik["warnung"] - statistik["kritisch"]
    if statistik["ok"] < 0:
        statistik["ok"] = 0

    freigegeben = statistik["kritisch"] == 0

    return befund, statistik, freigegeben


def schreibe_json(befund, statistik, freigegeben):
    os.makedirs(AUSGABE_DIR, exist_ok=True)
    pfad = os.path.join(AUSGABE_DIR, "CORE16_dry_run_ergebnis.json")
    out = {
        "meta": {
            "modul_id": "CORE-16",
            "name": "Dry-Run Validierung des Migrationsplans",
            "version": "1.0.0",
            "zeitstempel": datetime.now().isoformat(),
            "produktiv_freigegeben": False,
            "nur_pruefend": True,
        },
        "zusammenfassung": {
            "geprueft": statistik["geprueft"],
            "ok": statistik["ok"],
            "warnung": statistik["warnung"],
            "kritisch": statistik["kritisch"],
            "kopieren_vorgesehen": statistik["kopieren_vorgesehen"],
            "dry_run_freigegeben": freigegeben,
        },
        "befund": befund,
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"JSON geschrieben: {pfad}")
    return pfad


def schreibe_bericht(befund, statistik, freigegeben):
    os.makedirs(os.path.dirname(BERICHT_PFAD), exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-16 DRY-RUN VALIDIERUNG BERICHT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Zeitstempel: {datetime.now().isoformat()}\n")
        f.write(f"Geprueft: {statistik['geprueft']}\n")
        f.write(f"OK: {statistik['ok']}\n")
        f.write(f"Warnungen: {statistik['warnung']}\n")
        f.write(f"Kritisch: {statistik['kritisch']}\n")
        f.write(f"Kopieren vorgesehen: {statistik['kopieren_vorgesehen']}\n")
        f.write(f"Dry-Run FREIGEGEBEN: {freigegeben}\n\n")

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

        if not befund["kritisch"] and not befund["warnung"]:
            f.write("Keine Befunde. Dry-Run ist FREIGEGEBEN.\n\n")

        f.write("=" * 70 + "\n")
        f.write("ENDE BERICHT\n")
    log(f"Bericht geschrieben: {BERICHT_PFAD}")


def hauptlauf():
    log("Starte CORE-16 Dry-Run Validierung...")

    if not os.path.exists(PLAN_PFAD):
        log(f"FEHLER: Migrationsplan nicht gefunden: {PLAN_PFAD}")
        global FEHLER
        FEHLER += 1
        return

    log(f"Lade Migrationsplan: {PLAN_PFAD}")
    plan_data = lade_json(PLAN_PFAD)
    log(f"Migrationsplan geladen: {len(plan_data.get('plaene', []))} Eintraege")

    log("Validiere Plan...")
    befund, statistik, freigegeben = validiere_plan(plan_data)

    schreibe_json(befund, statistik, freigegeben)
    schreibe_bericht(befund, statistik, freigegeben)

    log("=" * 60)
    log("ZUSAMMENFASSUNG")
    log("=" * 60)
    log(f"Geprueft: {statistik['geprueft']}")
    log(f"OK: {statistik['ok']}")
    log(f"Warnungen: {statistik['warnung']}")
    log(f"Kritisch: {statistik['kritisch']}")
    log(f"Kopieren vorgesehen: {statistik['kopieren_vorgesehen']}")
    log(f"Dry-Run FREIGEGEBEN: {freigegeben}")
    log("=" * 60)

    if not freigegeben:
        log("WARNUNG: Dry-Run NICHT freigegeben. CORE-17 darf nicht kopieren.")
        global WARNUNGEN
        WARNUNGEN += 1
    else:
        log("Dry-Run FREIGEGEBEN. CORE-17 kann kopieren.")

    log("CORE-16 DRY-RUN VALIDIERUNG ABGESCHLOSSEN")


def selbsttest():
    print("CORE-16 SELBSTTEST =====================================")
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

    # Test validiere_plan mit Dummy-Daten
    dummy_plan = {
        "plaene": [
            {"relativer_pfad": "a.py", "ziel_pfad": "/ziel/a.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND",
             "sha256": "abc", "gesperrt": False, "kopieren": True},
            {"relativer_pfad": "b.py", "ziel_pfad": "/ziel/b.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND",
             "sha256": "def", "gesperrt": False, "kopieren": True},
        ],
        "konflikte": [],
    }
    befund, statistik, frei = validiere_plan(dummy_plan)
    t("Dummy-Plan freigegeben", frei is True)
    t("Dummy-Plan 2 geprueft", statistik["geprueft"] == 2)

    # Test mit Kollision
    dummy_plan2 = {
        "plaene": [
            {"relativer_pfad": "a.py", "ziel_pfad": "/ziel/x.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND",
             "sha256": "abc", "gesperrt": False, "kopieren": True},
            {"relativer_pfad": "b.py", "ziel_pfad": "/ziel/x.py", "zielentscheidung": "UEBERNEHMEN_KOPIEREND",
             "sha256": "def", "gesperrt": False, "kopieren": True},
        ],
        "konflikte": [],
    }
    befund2, _, frei2 = validiere_plan(dummy_plan2)
    t("Kollision erkannt", frei2 is False)
    t("Kollision kritisch", len(befund2["kritisch"]) > 0)

    print(f"\nFEHLER: {FEHLER}, WARNUNGEN: {WARNUNGEN}")
    print("=======================================================")
    return FEHLER == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    hauptlauf()
    sys.exit(0 if FEHLER == 0 else 1)
