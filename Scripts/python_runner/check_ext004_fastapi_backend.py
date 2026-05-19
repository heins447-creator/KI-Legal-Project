#!/usr/bin/env python3
"""
EXT-004 – FastAPI-Backend

Ziel:
Prüfung der Voraussetzungen fuer das FastAPI-Backend.

Sicherheit:
- Kein Cloud-Upload
- Keine Online-Anbindung
- Nur localhost (127.0.0.1)
- Keine echten Mandantendaten
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "Config" / "ext004_fastapi_backend_v1.json"
DB_PATH = BASE_DIR / "Database" / "DuckDB" / "alin_local.duckdb"


def pruefe() -> tuple[bool, list[str]]:
    fehler = []

    if not CONFIG_FILE.exists():
        fehler.append("Config fehlt")
        return False, fehler

    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fehler.append("Config ist ungueltiges JSON")
        return False, fehler

    # FastAPI prüfen
    try:
        import fastapi
    except ImportError:
        fehler.append("FastAPI nicht installiert")

    # Uvicorn prüfen
    try:
        import uvicorn
    except ImportError:
        fehler.append("Uvicorn nicht installiert")

    # DuckDB prüfen
    if not DB_PATH.exists():
        fehler.append("DuckDB-Datenbank nicht gefunden")
    else:
        try:
            import duckdb
            conn = duckdb.connect(str(DB_PATH))
            tabellen = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001' AND table_name IN ('terminologie', 'dokumente')"
            ).fetchall()
            tabellen_namen = {t[0] for t in tabellen}
            if "terminologie" not in tabellen_namen:
                fehler.append("Tabelle 'terminologie' fehlt")
            if "dokumente" not in tabellen_namen:
                fehler.append("Tabelle 'dokumente' fehlt")
            conn.close()
        except Exception as e:
            fehler.append(f"DuckDB-Fehler: {e}")

    # API-Verzeichnis prüfen (wird vom Runner erzeugt)
    api_dir = BASE_DIR / "ALIN_Neustart_Core" / "25_API_Backend"
    if not api_dir.exists():
        print("[WARNUNG] API-Verzeichnis noch nicht erzeugt (Runner muss zuerst laufen)")

    return (len(fehler) == 0, fehler)


def main() -> int:
    ok, fehler = pruefe()
    if ok:
        print("[OK] EXT-004 Check bestanden")
        return 0
    else:
        for f in fehler:
            print(f"[FEHLER] {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
