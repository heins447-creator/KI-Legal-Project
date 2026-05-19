#!/usr/bin/env python3
"""
Pruefdatei fuer CORE-10e – UI01 Abhaengigkeit
=============================================
Prueft, dass check_ui01_anwaltsansicht_v1 nur auf existierende Module verweist.
"""

import json
import sys
from pathlib import Path

def main():
    register_pfad = Path("ALIN_Neustart_Core/01_Register/modulregister.json")

    if not register_pfad.exists():
        print(f"FEHLER: {register_pfad} nicht gefunden")
        return 1

    with open(register_pfad, "r", encoding="utf-8") as f:
        data = json.load(f)

    modul_ids = {e["modul_id"] for e in data["eintraege"]}

    check_modul = None
    for entry in data["eintraege"]:
        if entry["modul_id"] == "check_ui01_anwaltsansicht_v1":
            check_modul = entry
            break

    if not check_modul:
        print("CORE-10e PRUEFUNG FEHLGESCHLAGEN")
        print("  check_ui01_anwaltsansicht_v1 nicht gefunden")
        return 1

    abhaengigkeiten = check_modul.get("abhaengigkeiten", [])
    fehlende = [dep for dep in abhaengigkeiten if dep not in modul_ids]

    if fehlende:
        print("CORE-10e PRUEFUNG FEHLGESCHLAGEN")
        print(f"  {len(fehlende)} fehlende Abhaengigkeit(en):")
        for f in fehlende:
            print(f"    - {f}")
        return 1
    else:
        print("CORE-10e PRUEFUNG BESTANDEN")
        print(f"  check_ui01_anwaltsansicht_v1 hat {len(abhaengigkeiten)} Abhaengigkeit(en)")
        print(f"  Alle sind im Register vorhanden: {abhaengigkeiten}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
