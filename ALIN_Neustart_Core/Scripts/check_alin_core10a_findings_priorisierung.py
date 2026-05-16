#!/usr/bin/env python3
"""
Pruefdatei fuer CORE-10a – Findings-Priorisierung
=================================================
Prueft, ob die Priorisierung korrekt erstellt wurde und alle
Kategorien (P0-P3) enthaelt.
"""

import json
import sys
from pathlib import Path

def main():
    log_pfad = Path("ALIN_Neustart_Core/Reports/ALIN_CORE10A_PRIORISIERUNG.json")
    bericht_pfad = Path("ALIN_Neustart_Core/Reports/ALIN_CORE10A_FINDINGS_PRIORISIERUNG_BERICHT.txt")
    
    fehler = []
    
    # 1. JSON-Export existiert
    if not log_pfad.exists():
        fehler.append(f"JSON-Export fehlt: {log_pfad}")
    else:
        with open(log_pfad, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 2. Alle Prioritaeten vorhanden
        for prio in ["P0", "P1", "P2", "P3"]:
            if prio not in data.get("priorisierung", {}):
                fehler.append(f"Prioritaet {prio} fehlt im JSON-Export")
        
        # 3. P0 enthaelt kritische Findings
        p0 = data.get("priorisierung", {}).get("P0", [])
        if not p0:
            fehler.append("P0 ist leer – erwartet wurden P02, P03, P10")
        
        # 4. Timestamp vorhanden
        if not data.get("timestamp"):
            fehler.append("Timestamp fehlt im JSON-Export")
    
    # 5. Textbericht existiert
    if not bericht_pfad.exists():
        fehler.append(f"Textbericht fehlt: {bericht_pfad}")
    else:
        with open(bericht_pfad, "r", encoding="utf-8") as f:
            inhalt = f.read()
        if "P0:" not in inhalt:
            fehler.append("Textbericht enthaelt keine P0-Sektion")
        if "P1:" not in inhalt:
            fehler.append("Textbericht enthaelt keine P1-Sektion")
        if "P2:" not in inhalt:
            fehler.append("Textbericht enthaelt keine P2-Sektion")
        if "P3:" not in inhalt:
            fehler.append("Textbericht enthaelt keine P3-Sektion")
    
    if fehler:
        print("CORE-10a PRUEFUNG FEHLGESCHLAGEN")
        for f in fehler:
            print(f"  - {f}")
        return 1
    else:
        print("CORE-10a PRUEFUNG BESTANDEN")
        print(f"  JSON-Export: {log_pfad}")
        print(f"  Textbericht: {bericht_pfad}")
        print(f"  P0-Eintraege: {len(p0)}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
