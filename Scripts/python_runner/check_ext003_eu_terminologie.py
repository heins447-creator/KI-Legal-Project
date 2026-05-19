#!/usr/bin/env python3
"""
EXT-003 – EU-Terminologiepaket

Ziel:
Aufbau eines lokalen EU-Terminologie-Registers für rechtssichere Übersetzungen.

Sicherheit:
- Kein Cloud-Übersetzungsdienst
- Keine Online-Terminologie-Abfragen
- EU-Daten nur aus lokalen Quellen
- Keine echten Mandantendaten für Validierung
"""

import json
import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("[FEHLER] DuckDB nicht installiert")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "Database" / "DuckDB"
DB_PATH = DB_DIR / "alin_local.duckdb"
CONFIG_FILE = BASE_DIR / "Config" / "ext003_eu_terminologie_v1.json"
MANIFEST_FILE = BASE_DIR / "ALIN_Neustart_Core" / "18_Terminologie" / "EU_TERMINOLOGIE_MANIFEST.json"


def pruefe() -> tuple[bool, list[str]]:
    fehler = []
    
    if not CONFIG_FILE.exists():
        fehler.append("Config fehlt")
        return False, fehler
    
    try:
        json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fehler.append("Config ist ungueltiges JSON")
        return False, fehler
    
    if not DB_PATH.exists():
        fehler.append("DuckDB-Datenbank nicht gefunden")
        return False, fehler
    
    try:
        conn = duckdb.connect(str(DB_PATH))
        
        # Prüfen, ob Tabelle existiert
        tabellen = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001' AND table_name = 'terminologie'"
        ).fetchall()
        if not tabellen:
            fehler.append("Tabelle 'terminologie' fehlt")
        
        conn.close()
    except Exception as e:
        fehler.append(f"DuckDB-Fehler: {e}")
    
    # Manifest prüfen (wird vom Runner erzeugt)
    if not MANIFEST_FILE.exists():
        print("[WARNUNG] Terminologie-Manifest noch nicht erzeugt (Runner muss zuerst laufen)")
    
    return (len(fehler) == 0, fehler)


def main() -> int:
    ok, fehler = pruefe()
    if ok:
        print("[OK] EXT-003 Check bestanden")
        return 0
    else:
        for f in fehler:
            print(f"[FEHLER] {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())