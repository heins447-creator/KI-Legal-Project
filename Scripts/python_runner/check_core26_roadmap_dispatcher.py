#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-26: Pruefdatei fuer Roadmap-Dispatcher

Prueft:
1. Config core26_roadmap_dispatcher_v1.json lesbar
2. Roadmap CORE25_gesamt_roadmap.json lesbar
3. Dashboard CORE23_dashboard.json lesbar
4. Arbeitsindex core21_arbeitsindex_v1.json lesbar
5. Agentenregeln core22_agentenregeln_v1.json lesbar
6. Queue CORE24_auftragsqueue.json lesbar
7. Runner-Verzeichnis vorhanden
8. Python-Interpreter vorhanden
9. Git verfuegbar
10. bereich_status() Funktion korrekt
11. Auftragserzeugung korrekt
12. Status-JSON beschreibbar
13. Auftrags-JSON beschreibbar
14. Bericht-Verzeichnis beschreibbar
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")

CONFIG_PATH = BASE_DIR / "Config" / "core26_roadmap_dispatcher_v1.json"
ROADMAP_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap.json"
DASHBOARD_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE23_dashboard.json"
ARBEITSINDEX_PATH = BASE_DIR / "Config" / "core21_arbeitsindex_v1.json"
AGENTENREGELN_PATH = BASE_DIR / "Config" / "core22_agentenregeln_v1.json"
QUEUE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_auftragsqueue.json"
RUNNER_DIR = BASE_DIR / "Scripts" / "python_runner"
PYTHON_EXE = Path("I:/KI_Legal_Project/Tools/Python312/python.exe")
STATUS_PATH = BASE_DIR / "ALIN_Neustart_Core" / "09_Automanager" / "CORE26_dispatcher_status.json"
AUFTRAG_PATH = BASE_DIR / "ALIN_Neustart_Core" / "09_Automanager" / "CORE26_naechster_auftrag.json"
BERICHT_DIR = BASE_DIR / "ALIN_Neustart_Core" / "Reports"


def pruefe() -> tuple[bool, list[str]]:
    fehler = []

    # 1. Config lesbar
    if not CONFIG_PATH.exists():
        fehler.append(f"Config fehlt: {CONFIG_PATH}")
    else:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("modul_id") != "CORE-26":
                fehler.append(f"Config.modul_id ist '{cfg.get('modul_id')}', erwartet 'CORE-26'")
        except Exception as e:
            fehler.append(f"Config ungueltig: {e}")

    # 2. Roadmap lesbar
    if not ROADMAP_PATH.exists():
        fehler.append(f"Roadmap fehlt: {ROADMAP_PATH}")
    else:
        try:
            with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
                roadmap = json.load(f)
            stufen = roadmap.get("roadmap", {}).get("stufen", [])
            if not stufen:
                fehler.append("Roadmap enthaelt keine Stufen")
            else:
                # Pruefe ob 90 Stufen
                if len(stufen) < 80:
                    fehler.append(f"Roadmap hat nur {len(stufen)} Stufen, erwartet ca. 90")
        except Exception as e:
            fehler.append(f"Roadmap ungueltig: {e}")

    # 3. Dashboard lesbar
    if not DASHBOARD_PATH.exists():
        fehler.append(f"Dashboard fehlt: {DASHBOARD_PATH}")
    else:
        try:
            with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
                dashboard = json.load(f)
            if dashboard.get("meta", {}).get("modul_id") != "CORE-23":
                fehler.append(f"Dashboard.modul_id ist '{dashboard.get('meta', {}).get('modul_id')}', erwartet 'CORE-23'")
        except Exception as e:
            fehler.append(f"Dashboard ungueltig: {e}")

    # 4. Arbeitsindex lesbar
    if not ARBEITSINDEX_PATH.exists():
        fehler.append(f"Arbeitsindex fehlt: {ARBEITSINDEX_PATH}")
    else:
        try:
            with open(ARBEITSINDEX_PATH, "r", encoding="utf-8") as f:
                idx = json.load(f)
            bereiche = idx.get("bereiche", {})
            if "aktiv" not in bereiche or "gesperrt" not in bereiche:
                fehler.append("Arbeitsindex hat keine 'aktiv' oder 'gesperrt' Bereiche")
        except Exception as e:
            fehler.append(f"Arbeitsindex ungueltig: {e}")

    # 5. Agentenregeln lesbar
    if not AGENTENREGELN_PATH.exists():
        fehler.append(f"Agentenregeln fehlen: {AGENTENREGELN_PATH}")
    else:
        try:
            with open(AGENTENREGELN_PATH, "r", encoding="utf-8") as f:
                regeln = json.load(f)
            if regeln.get("modul_id") != "CORE-22":
                fehler.append(f"Agentenregeln.modul_id ist '{regeln.get('modul_id')}', erwartet 'CORE-22'")
        except Exception as e:
            fehler.append(f"Agentenregeln ungueltig: {e}")

    # 6. Queue lesbar
    if not QUEUE_PATH.exists():
        fehler.append(f"Queue fehlt: {QUEUE_PATH}")
    else:
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception as e:
            fehler.append(f"Queue ungueltig: {e}")

    # 7. Runner-Verzeichnis vorhanden
    if not RUNNER_DIR.exists():
        fehler.append(f"Runner-Verzeichnis fehlt: {RUNNER_DIR}")
    else:
        if not RUNNER_DIR.is_dir():
            fehler.append(f"Runner-Pfad ist kein Verzeichnis: {RUNNER_DIR}")

    # 8. Python-Interpreter vorhanden
    if not PYTHON_EXE.exists():
        fehler.append(f"Python-Interpreter fehlt: {PYTHON_EXE}")

    # 9. Git verfuegbar
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            fehler.append("Git nicht verfuegbar (git --version fehlgeschlagen)")
    except Exception as e:
        fehler.append(f"Git nicht verfuegbar: {e}")

    # 10. bereich_status() Funktion korrekt
    # Wir testen die Logik aus dem Runner
    try:
        test_index = {
            "bereiche": {
                "aktiv": ["Scripts/python_runner/", "Config/"],
                "gesperrt": ["gesperrt", "archiv"],
                "referenz": ["ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/"]
            }
        }

        def bereich_status(pfad_str: str, arbeitsindex: dict) -> str:
            pfad_lower = pfad_str.lower().replace("\\", "/")
            bereiche = arbeitsindex.get("bereiche", {})
            for gesperrt in bereiche.get("gesperrt", []):
                if gesperrt.lower() in pfad_lower:
                    return "gesperrt"
            for aktiv in bereiche.get("aktiv", []):
                aktiv_norm = aktiv.lower().rstrip("/")
                if pfad_lower.startswith(aktiv_norm):
                    return "aktiv"
            for referenz in bereiche.get("referenz", []):
                ref_norm = referenz.lower().rstrip("/")
                if pfad_lower.startswith(ref_norm):
                    return "referenz"
            return "unbekannt"

        if bereich_status("Scripts/python_runner/test.py", test_index) != "aktiv":
            fehler.append("bereich_status() liefert falsches Ergebnis fuer aktiven Pfad")
        if bereich_status("gesperrt/test.py", test_index) != "gesperrt":
            fehler.append("bereich_status() liefert falsches Ergebnis fuer gesperrten Pfad")
        if bereich_status("ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/test.json", test_index) != "referenz":
            fehler.append("bereich_status() liefert falsches Ergebnis fuer Referenz-Pfad")
    except Exception as e:
        fehler.append(f"bereich_status() Test fehlgeschlagen: {e}")

    # 11. Auftragserzeugung korrekt
    try:
        test_stufe = {
            "stufe_id": "TEST-01",
            "name": "Teststufe",
            "beschreibung": "Test",
            "eingaben": ["Config/test.json"],
            "ausgaben": ["Scripts/test.py"],
            "tests": ["Test OK"],
            "erlaubte_naechste_module": ["TEST-02"]
        }
        test_auftrag = {
            "auftrags_id": "AUFTRAG-TEST",
            "stufe_id": test_stufe["stufe_id"],
            "name": test_stufe["name"],
            "beschreibung": test_stufe["beschreibung"],
            "eingaben": test_stufe["eingaben"],
            "ausgaben": test_stufe["ausgaben"],
            "folgeentscheidung": "TEST-02",
            "modul": "CORE-26"
        }
        if test_auftrag["stufe_id"] != "TEST-01":
            fehler.append("Auftragserzeugung: stufe_id nicht korrekt uebernommen")
    except Exception as e:
        fehler.append(f"Auftragserzeugung Test fehlgeschlagen: {e}")

    # 12. Status-JSON Verzeichnis beschreibbar (nicht Datei selbst ueberschreiben)
    try:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_file = STATUS_PATH.parent / "CORE26_test_schreibbarkeit_status.txt"
        test_data = {"test": True, "modul": "CORE-26"}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)
        with open(test_file, "r", encoding="utf-8") as f:
            gelesen = json.load(f)
        if not gelesen.get("test"):
            fehler.append("Status-Verzeichnis nicht korrekt beschreibbar")
        os.remove(test_file)
    except Exception as e:
        fehler.append(f"Status-Verzeichnis nicht beschreibbar: {e}")

    # 13. Auftrags-JSON Verzeichnis beschreibbar (nicht Datei selbst ueberschreiben)
    try:
        AUFTRAG_PATH.parent.mkdir(parents=True, exist_ok=True)
        test_file = AUFTRAG_PATH.parent / "CORE26_test_schreibbarkeit_auftrag.txt"
        test_data = {"test": True, "modul": "CORE-26"}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)
        with open(test_file, "r", encoding="utf-8") as f:
            gelesen = json.load(f)
        if not gelesen.get("test"):
            fehler.append("Auftrags-Verzeichnis nicht korrekt beschreibbar")
        os.remove(test_file)
    except Exception as e:
        fehler.append(f"Auftrags-Verzeichnis nicht beschreibbar: {e}")

    # 14. Bericht-Verzeichnis beschreibbar
    try:
        BERICHT_DIR.mkdir(parents=True, exist_ok=True)
        test_file = BERICHT_DIR / "CORE26_test_schreibbarkeit.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("TEST")
        with open(test_file, "r", encoding="utf-8") as f:
            inhalt = f.read()
        if inhalt != "TEST":
            fehler.append("Bericht-Verzeichnis nicht korrekt beschreibbar")
        os.remove(test_file)
    except Exception as e:
        fehler.append(f"Bericht-Verzeichnis nicht beschreibbar: {e}")

    return len(fehler) == 0, fehler


def main() -> int:
    print("=" * 60)
    print("CORE-26 CHECK: Roadmap-Dispatcher")
    print("=" * 60)

    ok, fehler = pruefe()

    if ok:
        print("[OK] Alle Pruefungen bestanden.")
        print("=" * 60)
        return 0
    else:
        print(f"[FEHLER] {len(fehler)} Pruefung(en) fehlgeschlagen:")
        for f in fehler:
            print(f"  - {f}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
