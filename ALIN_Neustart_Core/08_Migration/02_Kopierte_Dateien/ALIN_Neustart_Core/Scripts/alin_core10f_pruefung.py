#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10f Prüfdatei
Verifiziert dass keine generischen Platzhalter mehr im Modulregister vorhanden sind.
"""

import json
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"

GENERIC_EINGABE = "Konfiguration und Umgebungsvariablen."
GENERIC_AUSGABE = "Prozess-Start, Log-Datei, Exit-Code."


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("CORE-10f PRUEFUNG")
    print("=" * 60)

    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    eintraege = modulregister.get("eintraege", [])

    fehler = []
    generic_count = 0

    for m in eintraege:
        mid = m.get("modul_id", "")
        eingabe = m.get("eingabe", "")
        ausgabe = m.get("ausgabe", "")

        if eingabe == GENERIC_EINGABE and ausgabe == GENERIC_AUSGABE:
            generic_count += 1
            fehler.append(f"{mid}: Generischer Platzhalter eingabe/ausgabe")

    print(f"[OK] {len(eintraege)} Module geprueft")
    print(f"[OK] {generic_count} generische Platzhalter gefunden")

    print("=" * 60)
    if fehler:
        print(f"PRUEFUNG FEHLGESCHLAGEN – {len(fehler)} Fehler:")
        for f in fehler:
            print(f"  {f}")
        return 1
    else:
        print("PRUEFUNG BESTANDEN – Keine generischen Platzhalter mehr vorhanden")
        return 0


if __name__ == "__main__":
    sys.exit(main())
