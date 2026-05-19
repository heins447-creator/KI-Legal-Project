#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-24: Prüfdatei für den Autonomen Entwicklungsmanager

Prüft:
    1. Konfiguration vorhanden und valide JSON
    2. Dashboard vorhanden und valide JSON
    3. Arbeitsindex vorhanden und valide JSON
    4. Agentenregeln vorhanden und valide JSON
    5. Agentenfreigabe vorhanden
    6. Queue-Datei kann erstellt/gelesen werden
    7. Reparatur-Log kann erstellt/gelesen werden
    8. Bericht-Verzeichnis beschreibbar
    9. Python-Interpreter vorhanden
    10. Git verfügbar
    11. Erlaubte Auftragstypen sind definiert
    12. Verbotene Auftragstypen sind definiert
    13. Harte-Sperre-Bedingungen sind definiert
    14. Pfad-Prüfung funktioniert korrekt
    15. bereich_status() liefert erwartete Werte
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")
CONFIG_PATH = BASE_DIR / "Config" / "core24_entwicklungsmanager_v1.json"
DASHBOARD_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE23_dashboard.json"
ARBEITSINDEX_PATH = BASE_DIR / "Config" / "core21_arbeitsindex_v1.json"
AGENTENREGELN_PATH = BASE_DIR / "Config" / "core22_agentenregeln_v1.json"
AGENTEN_REGELN_MANIFEST_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE22_agenten_regeln.json"
AGENTENFREIGABE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "AGENTENFREIGABE_KLARSTELLUNG.txt"

QUEUE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_auftragsqueue.json"
REPARATUR_LOG_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_reparatur_log.json"
BERICHT_PATH = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt"
PYTHON_EXE = BASE_DIR / "Tools" / "Python312" / "python.exe"

fehler = []
warnungen = []
pruefungen = 0


def pruefe(bedingung: bool, meldung: str, ist_warnung: bool = False) -> None:
    global pruefungen
    pruefungen += 1
    if not bedingung:
        if ist_warnung:
            warnungen.append(meldung)
            print(f"  WARNUNG: {meldung}")
        else:
            fehler.append(meldung)
            print(f"  FEHLER: {meldung}")
    else:
        print(f"  OK: {meldung}")


def lade_json_sicher(pfad: Path) -> dict | None:
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None


def bereich_status(pfad: str, arbeitsindex: dict) -> str:
    pfad_norm = pfad.replace("\\", "/").lower()
    for bereich in arbeitsindex.get("bereiche", {}).get("aktiv", []):
        if pfad_norm.startswith(bereich.lower().rstrip("/") + "/") or pfad_norm == bereich.lower().rstrip("/"):
            return "aktiv"
    for bereich in arbeitsindex.get("bereiche", {}).get("referenz", []):
        if pfad_norm.startswith(bereich.lower().rstrip("/") + "/") or pfad_norm == bereich.lower().rstrip("/"):
            return "referenz"
    for bereich in arbeitsindex.get("bereiche", {}).get("gesperrt", []):
        if bereich.lower() in pfad_norm:
            return "gesperrt"
    return "unbekannt"


def main() -> int:
    print("=" * 80)
    print("CORE-24: PRÜFDATEI – Autonomer Entwicklungsmanager")
    print("=" * 80)

    # 1. Konfiguration
    print("\n[1] Konfiguration prüfen...")
    config = lade_json_sicher(CONFIG_PATH)
    pruefe(config is not None, f"Konfiguration lesbar: {CONFIG_PATH}")
    if config:
        pruefe(config.get("modul_id") == "CORE-24", "modul_id == CORE-24")
        pruefe("erlaubte_auftragstypen" in config, "erlaubte_auftragstypen definiert")
        pruefe("verbotene_auftragstypen" in config, "verbotene_auftragstypen definiert")
        pruefe("harte_sperre_bedingungen" in config, "harte_sperre_bedingungen definiert")
        pruefe("queue_regeln" in config, "queue_regeln definiert")
        pruefe("git_regeln" in config, "git_regeln definiert")
        pruefe("python_toolchain" in config, "python_toolchain definiert")

    # 2. Dashboard
    print("\n[2] Dashboard prüfen...")
    dashboard = lade_json_sicher(DASHBOARD_PATH)
    pruefe(dashboard is not None, f"Dashboard lesbar: {DASHBOARD_PATH}")
    if dashboard:
        pruefe("status_core_13_bis_22" in dashboard, "status_core_13_bis_22 vorhanden")
        pruefe("zulaessige_naechste_arbeiten" in dashboard, "zulaessige_naechste_arbeiten vorhanden")

    # 3. Arbeitsindex
    print("\n[3] Arbeitsindex prüfen...")
    arbeitsindex = lade_json_sicher(ARBEITSINDEX_PATH)
    pruefe(arbeitsindex is not None, f"Arbeitsindex lesbar: {ARBEITSINDEX_PATH}")
    if arbeitsindex:
        pruefe("bereiche" in arbeitsindex, "bereiche definiert")
        pruefe("aktiv" in arbeitsindex.get("bereiche", {}), "aktiv-Bereiche definiert")
        pruefe("referenz" in arbeitsindex.get("bereiche", {}), "referenz-Bereiche definiert")
        pruefe("gesperrt" in arbeitsindex.get("bereiche", {}), "gesperrt-Bereiche definiert")

    # 4. Agentenregeln
    print("\n[4] Agentenregeln prüfen...")
    agentenregeln = lade_json_sicher(AGENTENREGELN_PATH)
    pruefe(agentenregeln is not None, f"Agentenregeln lesbar: {AGENTENREGELN_PATH}")

    print("\n[5] Agenten-Regeln-Manifest prüfen...")
    agenten_regeln_manifest = lade_json_sicher(AGENTEN_REGELN_MANIFEST_PATH)
    pruefe(agenten_regeln_manifest is not None, f"Agenten-Regeln-Manifest lesbar: {AGENTEN_REGELN_MANIFEST_PATH}")

    # 5. Agentenfreigabe
    print("\n[6] Agentenfreigabe prüfen...")
    pruefe(AGENTENFREIGABE_PATH.exists(), f"Agentenfreigabe vorhanden: {AGENTENFREIGABE_PATH}")
    if AGENTENFREIGABE_PATH.exists():
        try:
            with open(AGENTENFREIGABE_PATH, "r", encoding="utf-8") as f:
                inhalt = f.read()
            pruefe("erlaubte befehle" in inhalt.lower() or "automatisch erlaubte" in inhalt.lower(),
                   "Agentenfreigabe enthält erlaubte Befehle")
        except Exception:
            pruefe(False, "Agentenfreigabe lesbar")

    # 6. Queue-Datei
    print("\n[7] Queue-Datei prüfen...")
    try:
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_queue = {"test": True}
        with open(QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(test_queue, f)
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            gelesen = json.load(f)
        pruefe(gelesen == test_queue, "Queue-Datei beschreibbar und lesbar")
    except Exception as e:
        pruefe(False, f"Queue-Datei beschreibbar: {e}")

    # 7. Reparatur-Log
    print("\n[8] Reparatur-Log prüfen...")
    try:
        REPARATUR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_log = {"test": True}
        with open(REPARATUR_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(test_log, f)
        with open(REPARATUR_LOG_PATH, "r", encoding="utf-8") as f:
            gelesen = json.load(f)
        pruefe(gelesen == test_log, "Reparatur-Log beschreibbar und lesbar")
    except Exception as e:
        pruefe(False, f"Reparatur-Log beschreibbar: {e}")

    # 8. Bericht-Verzeichnis
    print("\n[9] Bericht-Verzeichnis prüfen...")
    try:
        BERICHT_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_datei = BERICHT_PATH.parent / ".core24_test_write"
        with open(test_datei, "w", encoding="utf-8") as f:
            f.write("test")
        test_datei.unlink()
        pruefe(True, "Bericht-Verzeichnis beschreibbar")
    except Exception as e:
        pruefe(False, f"Bericht-Verzeichnis beschreibbar: {e}")

    # 9. Python-Interpreter
    print("\n[10] Python-Interpreter prüfen...")
    pruefe(PYTHON_EXE.exists(), f"Python-Interpreter vorhanden: {PYTHON_EXE}")
    if PYTHON_EXE.exists():
        try:
            result = subprocess.run([str(PYTHON_EXE), "--version"], capture_output=True, text=True, timeout=10)
            pruefe(result.returncode == 0, f"Python ausführbar: {result.stdout.strip()}")
        except Exception as e:
            pruefe(False, f"Python ausführbar: {e}")

    # 10. Git
    print("\n[11] Git prüfen...")
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
        pruefe(result.returncode == 0, f"Git verfügbar: {result.stdout.strip()}")
    except Exception as e:
        pruefe(False, f"Git verfügbar: {e}")

    # 11. Pfad-Prüfung (bereich_status)
    print("\n[12] Pfad-Prüfung (bereich_status) testen...")
    if arbeitsindex:
        pruefe(bereich_status("Scripts/python_runner/test.py", arbeitsindex) == "aktiv",
               "Scripts/python_runner/ -> aktiv")
        pruefe(bereich_status("ALIN_Neustart_Core/Reports/test.txt", arbeitsindex) == "aktiv",
               "ALIN_Neustart_Core/Reports/ -> aktiv")
        pruefe(bereich_status("ALIN_Neustart_Core/08_Migration/09_Manifest/test.json", arbeitsindex) == "referenz",
               "ALIN_Neustart_Core/08_Migration/09_Manifest/ -> referenz")
        pruefe(bereich_status("gesperrt/test.txt", arbeitsindex) == "gesperrt",
               "gesperrt/ -> gesperrt")
        pruefe(bereich_status("unbekannter_pfad/test.txt", arbeitsindex) == "unbekannt",
               "unbekannter_pfad/ -> unbekannt")
    else:
        pruefe(False, "bereich_status-Tests übersprungen (Arbeitsindex nicht geladen)", ist_warnung=True)

    # 12. Auftragstypen
    print("\n[13] Auftragstypen prüfen...")
    if config:
        erlaubt = config.get("erlaubte_auftragstypen", [])
        verboten = config.get("verbotene_auftragstypen", [])
        pruefe(len(erlaubt) > 0, f"Erlaubte Auftragstypen: {len(erlaubt)}")
        pruefe(len(verboten) > 0, f"Verbotene Auftragstypen: {len(verboten)}")
        # Keine Überschneidung
        ueberschneidung = set(erlaubt) & set(verboten)
        pruefe(len(ueberschneidung) == 0, f"Keine Überschneidung erlaubt/verboten: {ueberschneidung}")
    else:
        pruefe(False, "Auftragstypen-Tests übersprungen (Config nicht geladen)", ist_warnung=True)

    # 13. Harte-Sperre-Bedingungen
    print("\n[14] Harte-Sperre-Bedingungen prüfen...")
    if config:
        bedingungen = config.get("harte_sperre_bedingungen", [])
        pruefe(len(bedingungen) > 0, f"Harte-Sperre-Bedingungen definiert: {len(bedingungen)}")
        pruefe(any("3x" in b or "3" in b for b in bedingungen),
               "Mindestens eine 3-Versuche-Bedingung vorhanden")
    else:
        pruefe(False, "Harte-Sperre-Tests übersprungen (Config nicht geladen)", ist_warnung=True)

    # 14. Runner-Verzeichnis
    print("\n[15] Runner-Verzeichnis prüfen...")
    runner_dir = BASE_DIR / "Scripts" / "python_runner"
    pruefe(runner_dir.exists(), f"Runner-Verzeichnis vorhanden: {runner_dir}")
    if runner_dir.exists():
        py_dateien = list(runner_dir.glob("*.py"))
        pruefe(len(py_dateien) > 0, f"Python-Runner vorhanden: {len(py_dateien)} Dateien")

    # Zusammenfassung
    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print(f"Geprüft:     {pruefungen}")
    print(f"Fehler:      {len(fehler)}")
    print(f"Warnungen:   {len(warnungen)}")

    if fehler:
        print("\nFEHLERLISTE:")
        for i, f in enumerate(fehler, 1):
            print(f"  {i}. {f}")
        print("\nERGEBNIS: FEHLGESCHLAGEN")
        return 1
    else:
        print("\nERGEBNIS: ERFOLGREICH")
        if warnungen:
            print("\nWarnungen (nicht blockierend):")
            for w in warnungen:
                print(f"  - {w}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
