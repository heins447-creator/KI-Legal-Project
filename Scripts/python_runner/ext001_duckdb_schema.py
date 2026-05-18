#!/usr/bin/env python3
"""
EXT-001 – DuckDB-Schema für lokale Datenhaltung

Ziel:
Einfuehrung von DuckDB als lokale, dateibasierte analytische Datenbank.
Dieses Skript erzeugt die Datenbank und fuehrt das Schema aus.

Sicherheit:
- Kein Cloud-DB-Service
- Keine echten Mandantendaten
- Keine Remote-Verbindungen
- Nur lokale .duckdb-Dateien im Projektverzeichnis
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "Database" / "DuckDB"
MIGRATION_FILE = BASE_DIR / "Database" / "Migrations" / "100_duckdb_schema_ext001.sql"
CONFIG_FILE = BASE_DIR / "Config" / "ext001_duckdb_schema_v1.json"
REPORT_FILE = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "EXT001_DUCKDB_SCHEMA_BERICHT.txt"


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    print(f"[{zeitstempel()}] {msg}")


def lade_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"WARNUNG: Config nicht ladbar: {e}")
        return {}


def main() -> int:
    log("EXT-001 – DuckDB-Schema gestartet")

    config = lade_config()
    db_name = config.get("datenbank_name", "alin_local.duckdb")
    db_path = DB_DIR / db_name
    DB_DIR.mkdir(parents=True, exist_ok=True)

    log(f"Datenbankpfad: {db_path}")

    if not MIGRATION_FILE.exists():
        log(f"FEHLER: Migration nicht gefunden: {MIGRATION_FILE}")
        return 1

    migration_sql = MIGRATION_FILE.read_text(encoding="utf-8")
    log(f"Migration geladen: {len(migration_sql)} Zeichen")

    try:
        conn = duckdb.connect(str(db_path))
        log("Verbindung hergestellt")

        # Schema ausführen (idempotent durch IF NOT EXISTS)
        conn.execute(migration_sql)
        log("Schema-Migration ausgefuehrt")

        # Tabellen validieren
        tabellen = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001'"
        ).fetchall()
        tabelle_namen = [t[0] for t in tabellen]
        log(f"Tabellen gefunden: {tabelle_namen}")

        erwartet = ["dokumente", "ocr_ergebnisse", "uebersetzungen", "terminologie", "vektor_embeddings"]
        fehlend = [t for t in erwartet if t not in tabelle_namen]
        if fehlend:
            log(f"FEHLER: Fehlende Tabellen: {fehlend}")
            return 1

        # View validieren
        views = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001' AND table_type = 'VIEW'"
        ).fetchall()
        view_namen = [v[0] for v in views]
        log(f"Views gefunden: {view_namen}")

        if "v_dokumente_vollstaendigkeit" not in view_namen:
            log("FEHLER: View v_dokumente_vollstaendigkeit fehlt")
            return 1

        # Test-Datensatz prüfen
        test = conn.execute(
            "SELECT COUNT(*) FROM alin_ext001.dokumente WHERE dokument_id = '00000000-0000-0000-0000-000000000001'"
        ).fetchone()
        if test and test[0] == 1:
            log("Test-Datensatz vorhanden")
        else:
            log("WARNUNG: Test-Datensatz nicht gefunden")

        # Indizes prüfen
        indizes = conn.execute(
            "SELECT index_name FROM duckdb_indexes() WHERE schema_name = 'alin_ext001'"
        ).fetchall()
        index_namen = [i[0] for i in indizes]
        log(f"Indizes gefunden: {len(index_namen)}")

        conn.close()
        log("Verbindung geschlossen")

    except Exception as e:
        log(f"FEHLER bei DuckDB-Operation: {e}")
        return 1

    # Bericht schreiben
    bericht = f"""EXT-001 – DuckDB-Schema Bericht
Erzeugt: {zeitstempel()}
Datenbank: {db_path}
Migration: {MIGRATION_FILE}

Tabellen: {tabelle_namen}
Views: {view_namen}
Indizes: {len(index_namen)}
Fehlende Tabellen: {fehlend if 'fehlend' in dir() else 'keine'}

Status: ERFOLGREICH
"""
    REPORT_FILE.write_text(bericht, encoding="utf-8")
    log(f"Bericht geschrieben: {REPORT_FILE}")

    log("EXT-001 abgeschlossen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
