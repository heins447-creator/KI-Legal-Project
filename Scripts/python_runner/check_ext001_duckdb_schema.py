#!/usr/bin/env python3
"""
EXT-001 – Check-Datei für DuckDB-Schema

Hinweis: Die Datenbank wird vom Runner erzeugt. Dieser Check validiert
nur die Voraussetzungen (Dateien vorhanden, Config valide) und prüft
die Datenbankstruktur, falls sie bereits existiert.
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
MIGRATION_FILE = BASE_DIR / "Database" / "Migrations" / "100_duckdb_schema_ext001.sql"
CONFIG_FILE = BASE_DIR / "Config" / "ext001_duckdb_schema_v1.json"

def pruefe() -> tuple[bool, list[str]]:
    fehler = []
    warnungen = []
    
    # 1. Migration existiert
    if not MIGRATION_FILE.exists():
        fehler.append("Migration fehlt")
        return False, fehler
    
    # 2. Config existiert und ist valides JSON
    if not CONFIG_FILE.exists():
        fehler.append("Config fehlt")
        return False, fehler
    
    try:
        json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fehler.append("Config ist ungueltiges JSON")
        return False, fehler
    
    # 3. Datenbank validieren (falls bereits erzeugt)
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    db_name = config.get("datenbank_name", "alin_local.duckdb")
    db_path = DB_DIR / db_name
    
    if not db_path.exists():
        warnungen.append("Datenbank noch nicht erzeugt (Runner muss zuerst laufen)")
        print(f"[WARNUNG] {warnungen[-1]}")
        # Kein Fehler – Runner wird die DB erzeugen
    else:
        try:
            conn = duckdb.connect(str(db_path))
            
            # Tabellen prüfen
            tabellen = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001' AND table_type = 'BASE TABLE'"
            ).fetchall()
            tabelle_namen = [t[0] for t in tabellen]
            erwartet = ["dokumente", "ocr_ergebnisse", "uebersetzungen", "terminologie", "vektor_embeddings"]
            for t in erwartet:
                if t not in tabelle_namen:
                    fehler.append(f"Tabelle '{t}' fehlt")
            
            # View prüfen
            views = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001' AND table_type = 'VIEW'"
            ).fetchall()
            view_namen = [v[0] for v in views]
            if "v_dokumente_vollstaendigkeit" not in view_namen:
                fehler.append("View v_dokumente_vollstaendigkeit fehlt")
            
            # Schema-Indizes prüfen
            indizes = conn.execute(
                "SELECT index_name FROM duckdb_indexes() WHERE schema_name = 'alin_ext001'"
            ).fetchall()
            if len(indizes) < 6:
                fehler.append(f"Zu wenig Indizes: {len(indizes)} (erwartet >= 6)")
            
            conn.close()
        except Exception as e:
            fehler.append(f"DuckDB-Fehler: {e}")
    
    return (len(fehler) == 0, fehler)

def main() -> int:
    ok, fehler = pruefe()
    if ok:
        print("[OK] EXT-001 Check bestanden")
        return 0
    else:
        for f in fehler:
            print(f"[FEHLER] {f}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
