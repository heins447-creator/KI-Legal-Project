#!/usr/bin/env python3
"""
EXT-005 – Semantische Suche Check

Ziel:
Pruefung der Voraussetzungen fuer semantische Suche.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "Config" / "ext005_semantische_suche_v1.json"
DB_PATH = BASE_DIR / "Database" / "DuckDB" / "alin_local.duckdb"

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
        import duckdb
        conn = duckdb.connect(str(DB_PATH))
        tabellen = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'alin_ext001' AND table_name IN ('terminologie', 'ocr_ergebnisse', 'vektor_embeddings')"
        ).fetchall()
        tabellen_namen = {t[0] for t in tabellen}
        if "terminologie" not in tabellen_namen:
            fehler.append("Tabelle 'terminologie' fehlt")
        if "ocr_ergebnisse" not in tabellen_namen:
            fehler.append("Tabelle 'ocr_ergebnisse' fehlt")
        if "vektor_embeddings" not in tabellen_namen:
            fehler.append("Tabelle 'vektor_embeddings' fehlt")
        conn.close()
    except Exception as e:
        fehler.append(f"DuckDB-Fehler: {e}")

    # NumPy pruefen
    try:
        import numpy
    except ImportError:
        fehler.append("NumPy nicht installiert")

    return (len(fehler) == 0, fehler)

def main() -> int:
    ok, fehler = pruefe()
    if ok:
        print("[OK] EXT-005 Check bestanden")
        return 0
    else:
        for f in fehler:
            print(f"[FEHLER] {f}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
