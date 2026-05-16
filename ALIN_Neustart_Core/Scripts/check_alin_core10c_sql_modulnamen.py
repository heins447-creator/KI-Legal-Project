#!/usr/bin/env python3
"""
Pruefdatei fuer CORE-10c – SQL-Modulnamen bereinigen
====================================================
Prueft, ob alle 20 Module mit SQL-Code als modulname korrigiert wurden.
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
    
    fehler = []
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "COUNT", "FROM", "WHERE"]
    
    for entry in data.get("eintraege", []):
        modulname = entry.get("modulname", "")
        modul_id = entry.get("modul_id", "")
        if any(kw in modulname.upper() for kw in sql_keywords):
            fehler.append(f"  {modul_id}: modulname='{modulname}'")
    
    if fehler:
        print("CORE-10c PRUEFUNG FEHLGESCHLAGEN")
        print(f"Noch {len(fehler)} Module mit SQL-Code als modulname:")
        for f in fehler:
            print(f)
        return 1
    else:
        print("CORE-10c PRUEFUNG BESTANDEN")
        print("  Keine SQL-Fragmente mehr als modulname gefunden.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
