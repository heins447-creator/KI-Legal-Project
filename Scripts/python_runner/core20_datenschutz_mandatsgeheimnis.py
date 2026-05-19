#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-20 / STUFE-020: Datenschutz und Mandatsgeheimnis - Python-Runner

Ziel:
    Validiert die existierenden Dateien im Verzeichnis
    ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis und erzeugt
    einen Bericht unter ALIN_Neustart_Core/Reports/.

Lieferpflichten aus AGENTS.md:
    - Python-Laeufer unter Scripts/python_runner/
    - Bericht unter ALIN_Neustart_Core/Reports/
    - Keine destruktiven Operationen
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")
TARGET_DIR = BASE_DIR / "ALIN_Neustart_Core" / "20_Datenschutz_Mandatsgeheimnis"
REPORT_PATH = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE20_DATENSCHUTZ_MANDATSGEHEIMNIS_BERICHT.txt"
SCHEMA_PATH = TARGET_DIR / "DATENSCHUTZ_MARKIERUNGEN.schema.json"
MANDAT_PATH = TARGET_DIR / "MANDATSGEHEIMNIS_REGELN.md"
EXPORT_PATH = TARGET_DIR / "EXPORTREGELN.md"


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log_bericht(lines: list[str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def validate_schema() -> tuple[bool, list[str]]:
    fehler = []
    if not SCHEMA_PATH.exists():
        fehler.append(f"Schema nicht gefunden: {SCHEMA_PATH}")
        return False, fehler
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        fehler.append(f"Schema ungueltiges JSON: {e}")
        return False, fehler
    except Exception as e:
        fehler.append(f"Schema Lesefehler: {e}")
        return False, fehler

    # Pflichtfelder pruefen
    required = schema.get("required", [])
    for field in ["schema_version", "markierung_id", "objekt_id", "markierungen"]:
        if field not in required:
            fehler.append(f"Schema: Pflichtfeld '{field}' fehlt in 'required'")

    # Markierungen-Enum pruefen
    props = schema.get("properties", {})
    markierungen = props.get("markierungen", {})
    items = markierungen.get("items", {})
    enum = items.get("enum", [])
    erwartet = {
        "mandatsbezogen",
        "personenbezogen",
        "besonders_schutzbeduerftig",
        "nur_lokal",
        "nicht_exportieren",
        "nicht_an_externe_modelle",
        "cloud_verboten"
    }
    actual = set(enum)
    if actual != erwartet:
        fehlend = erwartet - actual
        zuviel = actual - erwartet
        if fehlend:
            fehler.append(f"Schema: Markierungen fehlen: {fehlend}")
        if zuviel:
            fehler.append(f"Schema: Unerwartete Markierungen: {zuviel}")

    return len(fehler) == 0, fehler


def validate_markdown(pfad: Path, titel: str) -> tuple[bool, list[str]]:
    fehler = []
    if not pfad.exists():
        fehler.append(f"{titel} nicht gefunden: {pfad}")
        return False, fehler
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        fehler.append(f"{titel} Lesefehler: {e}")
        return False, fehler

    if not content.strip():
        fehler.append(f"{titel} ist leer")
    if "# " not in content:
        fehler.append(f"{titel} hat keine Hauptueberschrift (# )")
    if "## " not in content:
        fehler.append(f"{titel} hat keine Abschnittsueberschrift (## )")

    return len(fehler) == 0, fehler


def main() -> int:
    ts = zeitstempel()
    lines = []
    lines.append("=" * 80)
    lines.append("CORE-20 / STUFE-020: DATENSCHUTZ UND MANDATSGEHEIMNIS BERICHT")
    lines.append("=" * 80)
    lines.append(f"Zeitstempel: {ts}")
    lines.append("")

    # 1. Schema validieren
    ok_schema, fehler_schema = validate_schema()
    lines.append("SCHEMA-VALIDIERUNG (DATENSCHUTZ_MARKIERUNGEN.schema.json):")
    if ok_schema:
        lines.append("  OK: Schema ist gueltig und vollstaendig.")
    else:
        for f in fehler_schema:
            lines.append(f"  FEHLER: {f}")
    lines.append("")

    # 2. Mandatsgeheimnis-Regeln validieren
    ok_mandat, fehler_mandat = validate_markdown(MANDAT_PATH, "MANDATSGEHEIMNIS_REGELN.md")
    lines.append("MANDATSGEHEIMNIS-REGELN:")
    if ok_mandat:
        lines.append("  OK: Datei vorhanden und strukturiert.")
    else:
        for f in fehler_mandat:
            lines.append(f"  FEHLER: {f}")
    lines.append("")

    # 3. Exportregeln validieren
    ok_export, fehler_export = validate_markdown(EXPORT_PATH, "EXPORTREGELN.md")
    lines.append("EXPORTREGELN:")
    if ok_export:
        lines.append("  OK: Datei vorhanden und strukturiert.")
    else:
        for f in fehler_export:
            lines.append(f"  FEHLER: {f}")
    lines.append("")

    # 4. Verzeichnisstruktur
    lines.append("VERZEICHNISSTRUKTUR:")
    if TARGET_DIR.exists():
        lines.append(f"  OK: Zielverzeichnis existiert: {TARGET_DIR}")
        for f in sorted(TARGET_DIR.iterdir()):
            lines.append(f"    - {f.name}")
    else:
        lines.append(f"  FEHLER: Zielverzeichnis fehlt: {TARGET_DIR}")
    lines.append("")

    # Zusammenfassung
    gesamt_ok = ok_schema and ok_mandat and ok_export
    lines.append("ZUSAMMENFASSUNG:")
    lines.append(f"  Schema:      {'OK' if ok_schema else 'FEHLER'}")
    lines.append(f"  Mandat:      {'OK' if ok_mandat else 'FEHLER'}")
    lines.append(f"  Export:      {'OK' if ok_export else 'FEHLER'}")
    lines.append(f"  Gesamt:      {'ERFOLG' if gesamt_ok else 'FEHLER'}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("ENDE BERICHT")
    lines.append("=" * 80)

    log_bericht(lines)
    print(f"[{ts}] Bericht geschrieben: {REPORT_PATH}")
    return 0 if gesamt_ok else 1


if __name__ == "__main__":
    sys.exit(main())
