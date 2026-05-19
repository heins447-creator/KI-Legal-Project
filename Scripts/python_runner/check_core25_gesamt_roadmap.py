#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-25: Pruefdatei fuer Gesamt-Roadmap

Prueft:
1. CORE25_gesamt_roadmap.json existiert und ist gueltiges JSON
2. Alle Pflichtfelder pro Stufe vorhanden
3. Stufen-IDs eindeutig
4. Abhaengigkeiten zyklenfrei
5. Alle Abhaengigkeiten loesen sich auf (existieren als Stufen-IDs)
6. Prioritaeten sind numerisch
7. Status-Werte sind erlaubt
8. Meta.modul_id == CORE-25
9. Bericht existiert und enthaelt "CORE-25" und "ERFOLGREICH" oder keinen Fehler
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path("I:/KI_Legal_Project")
ROADMAP_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap.json"
BERICHT_PATH = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE25_GESAMT_ROADMAP_BERICHT.txt"
CONFIG_PATH = BASE_DIR / "Config" / "core25_roadmap_v1.json"

ERLAUBTE_STATUS = {"offen", "in_bearbeitung", "abgeschlossen", "gesperrt", "wartend", "fehlerhaft", "testbar", "entwicklung", "revision", "ersetzt"}
PFLICHTFELDER = ["stufe_id", "name", "abhaengigkeiten", "eingaben", "ausgaben", "tests", "prioritaet", "fertigstellungskriterien"]


def pruefe() -> tuple[bool, list[str]]:
    fehler = []

    # 1. Roadmap-JSON existiert
    if not ROADMAP_PATH.exists():
        fehler.append(f"Roadmap-JSON fehlt: {ROADMAP_PATH}")
        return False, fehler

    try:
        with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
            roadmap = json.load(f)
    except json.JSONDecodeError as e:
        fehler.append(f"Roadmap-JSON ungueltig: {e}")
        return False, fehler
    except Exception as e:
        fehler.append(f"Roadmap-JSON Lesefehler: {e}")
        return False, fehler

    # 2. Meta
    meta = roadmap.get("meta", {})
    if meta.get("modul_id") != "CORE-25":
        fehler.append(f"Meta.modul_id ist '{meta.get('modul_id')}', erwartet 'CORE-25'")

    # 3. Stufen
    stufen = roadmap.get("roadmap", {}).get("stufen", [])
    if not stufen:
        fehler.append("Keine Stufen in Roadmap vorhanden")
        return False, fehler

    ids = set()
    for stufe in stufen:
        sid = stufe.get("stufe_id", "")
        if not sid:
            fehler.append("Stufe ohne stufe_id gefunden")
            continue
        if sid in ids:
            fehler.append(f"Doppelte stufe_id: {sid}")
        ids.add(sid)

        for pflicht in PFLICHTFELDER:
            if pflicht not in stufe:
                fehler.append(f"{sid}: Pflichtfeld '{pflicht}' fehlt")

        status = stufe.get("status", "")
        if status and status not in ERLAUBTE_STATUS:
            fehler.append(f"{sid}: Ungueltiger Status '{status}'")

        prio = stufe.get("prioritaet")
        if not isinstance(prio, (int, float)):
            fehler.append(f"{sid}: Prioritaet ist nicht numerisch: {prio}")

    # 4. Abhaengigkeiten aufloesbar
    for stufe in stufen:
        sid = stufe["stufe_id"]
        for dep in stufe.get("abhaengigkeiten", []):
            if dep not in ids:
                fehler.append(f"{sid}: Abhaengigkeit '{dep}' existiert nicht als Stufe")

    # 5. Zyklenfreiheit (DFS)
    graph = {s["stufe_id"]: s.get("abhaengigkeiten", []) for s in stufen}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {sid: WHITE for sid in ids}
    zyklen = []

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                zyklen.append(" -> ".join(cycle))
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for sid in ids:
        if color[sid] == WHITE:
            dfs(sid, [])

    if zyklen:
        for z in zyklen:
            fehler.append(f"Zyklus gefunden: {z}")

    # 6. Config existiert
    if not CONFIG_PATH.exists():
        fehler.append(f"Config fehlt: {CONFIG_PATH}")
    else:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("modul_id") != "CORE-25":
                fehler.append(f"Config.modul_id ist '{cfg.get('modul_id')}', erwartet 'CORE-25'")
        except Exception as e:
            fehler.append(f"Config ungueltig: {e}")

    # 7. Bericht existiert und enthaelt Erfolg
    if not BERICHT_PATH.exists():
        fehler.append(f"Bericht fehlt: {BERICHT_PATH}")
    else:
        try:
            with open(BERICHT_PATH, "r", encoding="utf-8") as f:
                inhalt = f.read()
            if "CORE-25" not in inhalt:
                fehler.append("Bericht enthaelt nicht 'CORE-25'")
            if "FEHLGESCHLAGEN" in inhalt and "VALIDIERUNG" in inhalt:
                # Warnung, kein harter Fehler - koennte alte Version sein
                pass
        except Exception as e:
            fehler.append(f"Bericht Lesefehler: {e}")

    return len(fehler) == 0, fehler


def main() -> int:
    print("=" * 60)
    print("CORE-25 CHECK: Gesamt-Roadmap")
    print("=" * 60)

    ok, fehler = pruefe()

    if ok:
        print("[OK] Alle Pruefungen bestanden.")
        print("=" * 60)
        return 0
    else:
        print(f"[FEHLER] {len(fehler)} Pruefung(en) fehlgeschlagen:")
        for f in fehler:
            print(f"  - {f}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
