#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-20 / STUFE-020: Pruefdatei fuer Datenschutz und Mandatsgeheimnis

Prueft:
1. Zielverzeichnis existiert
2. Schema-Datei ist gueltiges JSON
3. Mandatsgeheimnis-Regeln sind lesbar und strukturiert
4. Exportregeln sind lesbar und strukturiert
5. Bericht-Verzeichnis ist beschreibbar
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")
TARGET_DIR = BASE_DIR / "ALIN_Neustart_Core" / "20_Datenschutz_Mandatsgeheimnis"
REPORT_DIR = BASE_DIR / "ALIN_Neustart_Core" / "Reports"


def pruefe() -> tuple[bool, list[str]]:
    fehler = []

    # 1. Verzeichnis existiert
    if not TARGET_DIR.exists():
        fehler.append(f"Zielverzeichnis fehlt: {TARGET_DIR}")
    else:
        if not TARGET_DIR.is_dir():
            fehler.append(f"Zielpfad ist kein Verzeichnis: {TARGET_DIR}")

    # 2. Schema-Datei
    schema_path = TARGET_DIR / "DATENSCHUTZ_MARKIERUNGEN.schema.json"
    if not schema_path.exists():
        fehler.append(f"Schema fehlt: {schema_path}")
    else:
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            if schema.get("type") != "object":
                fehler.append("Schema: type ist nicht 'object'")
            if "required" not in schema:
                fehler.append("Schema: 'required' fehlt")
            if "properties" not in schema:
                fehler.append("Schema: 'properties' fehlt")
        except json.JSONDecodeError as e:
            fehler.append(f"Schema ungueltiges JSON: {e}")
        except Exception as e:
            fehler.append(f"Schema Lesefehler: {e}")

    # 3. Mandatsgeheimnis-Regeln
    mandat_path = TARGET_DIR / "MANDATSGEHEIMNIS_REGELN.md"
    if not mandat_path.exists():
        fehler.append(f"Mandatsgeheimnis-Regeln fehlen: {mandat_path}")
    else:
        try:
            with open(mandat_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                fehler.append("Mandatsgeheimnis-Regeln sind leer")
            if "# " not in content:
                fehler.append("Mandatsgeheimnis-Regeln haben keine Hauptueberschrift")
        except Exception as e:
            fehler.append(f"Mandatsgeheimnis-Regeln Lesefehler: {e}")

    # 4. Exportregeln
    export_path = TARGET_DIR / "EXPORTREGELN.md"
    if not export_path.exists():
        fehler.append(f"Exportregeln fehlen: {export_path}")
    else:
        try:
            with open(export_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                fehler.append("Exportregeln sind leer")
            if "# " not in content:
                fehler.append("Exportregeln haben keine Hauptueberschrift")
        except Exception as e:
            fehler.append(f"Exportregeln Lesefehler: {e}")

    # 5. Bericht-Verzeichnis beschreibbar
    if not REPORT_DIR.exists():
        try:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            fehler.append(f"Bericht-Verzeichnis nicht beschreibbar: {e}")

    return len(fehler) == 0, fehler


def main() -> int:
    ok, fehler = pruefe()
    print("=" * 60)
    print("CORE-20 CHECK: Datenschutz und Mandatsgeheimnis")
    print("=" * 60)
    if ok:
        print("[OK] Alle Pruefungen bestanden.")
        return 0
    else:
        for f in fehler:
            print(f"[FEHLER] {f}")
        print(f"\nGesamt: {len(fehler)} Fehler")
        return 1


if __name__ == "__main__":
    sys.exit(main())
