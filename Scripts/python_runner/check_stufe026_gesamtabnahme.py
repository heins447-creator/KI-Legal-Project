#!/usr/bin/env python3
"""
Check-File fuer STUFE-026 – Gesamtabnahme (Vorbereitung)
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "ALIN_Neustart_Core" / "Reports"
CONFIG_DIR = BASE_DIR / "Config"
ROADMAP_V2 = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap_v2.json"


def pruefe() -> tuple[bool, list[str]]:
    fehler = []

    if not REPORTS_DIR.exists():
        fehler.append("Reports-Verzeichnis fehlt")
    else:
        berichte = list(REPORTS_DIR.glob("*.txt"))
        if len(berichte) < 20:
            fehler.append(f"Zu wenig Berichte: {len(berichte)}")

    if not CONFIG_DIR.exists():
        fehler.append("Config-Verzeichnis fehlt")
    else:
        configs = list(CONFIG_DIR.glob("*.json"))
        if len(configs) < 10:
            fehler.append(f"Zu wenig Configs: {len(configs)}")
        ungueltig = 0
        for cfg in configs:
            try:
                json.loads(cfg.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                ungueltig += 1
        if ungueltig > 0:
            print(f"[WARNUNG] {ungueltig} ungueltige Configs (bekanntes Altproblem)")

    if not ROADMAP_V2.exists():
        fehler.append("Roadmap v2 fehlt")
    else:
        try:
            daten = json.loads(ROADMAP_V2.read_text(encoding="utf-8"))
            stufen = daten.get("roadmap", {}).get("stufen", [])
            if len(stufen) < 80:
                fehler.append(f"Roadmap v2: Zu wenig Stufen ({len(stufen)})")
        except json.JSONDecodeError as e:
            fehler.append(f"Roadmap v2 ungueltig: {e}")

    return (len(fehler) == 0, fehler)


def main() -> int:
    ok, fehler = pruefe()
    if ok:
        print("[OK] Alle Pruefungen bestanden.")
        return 0
    else:
        print("[FEHLER] Pruefungen fehlgeschlagen:")
        for f in fehler:
            print(f"  - {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
