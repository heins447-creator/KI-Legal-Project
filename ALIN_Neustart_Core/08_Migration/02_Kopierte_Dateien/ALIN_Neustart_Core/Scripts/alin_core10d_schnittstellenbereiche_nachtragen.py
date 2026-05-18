#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10d: Schnittstellenbereiche nachtragen
Analyseskript – prüft Schnittstellenregister und ordnet Module zu.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"
REPORT_PATH = ROOT / "ALIN_Neustart_Core" / "Reports" / "ALIN_CORE10D_SCHNITTSTELLENBEREICHE_BERICHT.txt"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("CORE-10d SCHNITTSTELLENBEREICHE ANALYSE")
    print("=" * 70)

    schnittstellenregister = load_json(REGISTER_DIR / "schnittstellenregister.json")
    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    ressourcenregister = load_json(REGISTER_DIR / "ressourcenregister.json")
    toolregister = load_json(REGISTER_DIR / "toolregister.json")

    # Indexe
    modul_ids = {m["modul_id"] for m in modulregister.get("eintraege", [])}
    res_ids = {r["resource_id"] for r in ressourcenregister.get("eintraege", [])}
    tool_ids = {t["tool_id"] for t in toolregister.get("eintraege", [])}

    schnittstellen = schnittstellenregister.get("eintraege", [])

    report_lines = [
        "=" * 70,
        "CORE-10d SCHNITTSTELLENBEREICHE ANALYSEBERICHT",
        "=" * 70,
        f"Erstellt: 2026-05-16",
        f"Analysierte Schnittstellen: {len(schnittstellen)}",
        "",
        "1. SCHNITTSTELLEN-UEBERSICHT",
        "-" * 40,
    ]

    status_counts = {"aktiv": 0, "vorbereitet": 0, "platzhalter": 0, "gesperrt": 0, "pruefung_erforderlich": 0}
    cloud_gesperrt = 0
    cloud_manuell = 0
    deepl_mentioned = False

    for si in schnittstellen:
        sid = si["schnittstelle_id"]
        name = si["name"]
        status = si["status"]
        bereich = si["bereich"]
        cloud_status = si.get("cloud_status", "keiner")
        status_counts[status] = status_counts.get(status, 0) + 1

        if cloud_status == "gesperrt":
            cloud_gesperrt += 1
        elif cloud_status == "manuell_freigabepflichtig":
            cloud_manuell += 1

        if "DEEPL_API" in str(si) or "deepl" in si.get("risikohinweis", "").lower():
            deepl_mentioned = True

        # Prüfe beteiligte Module
        module_ok = 0
        module_missing = 0
        for m in si.get("beteiligte_module", []):
            if m in modul_ids:
                module_ok += 1
            else:
                module_missing += 1

        # Prüfe Ressourcen
        res_ok = 0
        res_missing = 0
        for r in si.get("benoetigte_ressourcen", []):
            if r in res_ids:
                res_ok += 1
            else:
                res_missing += 1

        # Prüfe Tools
        tool_ok = 0
        tool_missing = 0
        for t in si.get("benoetigte_tools", []):
            if t in tool_ids:
                tool_ok += 1
            else:
                tool_missing += 1

        report_lines.append(f"  {sid} [{status}]")
        report_lines.append(f"    Bereich: {bereich}, Cloud: {cloud_status}")
        report_lines.append(f"    Module: {module_ok} ok, {module_missing} fehlend")
        report_lines.append(f"    Ressourcen: {res_ok} ok, {res_missing} fehlend")
        report_lines.append(f"    Tools: {tool_ok} ok, {tool_missing} fehlend")
        report_lines.append("")

    report_lines.extend([
        "2. STATUS-VERTEILUNG",
        "-" * 40,
    ])
    for st, cnt in status_counts.items():
        if cnt > 0:
            report_lines.append(f"  {st}: {cnt}")

    report_lines.extend([
        "",
        "3. CLOUD-/ONLINE-SCHNITTSTELLEN",
        "-" * 40,
        f"  Gesperrt: {cloud_gesperrt}",
        f"  Manuell freigabepflichtig: {cloud_manuell}",
        f"  DEEPL_API in Hinweisen: {'JA' if deepl_mentioned else 'NEIN'}",
        "",
        "4. ZUSAMMENFASSUNG",
        "-" * 40,
        f"  Gesamt-Schnittstellen: {len(schnittstellen)}",
        f"  Aktiv: {status_counts.get('aktiv', 0)}",
        f"  Vorbereitet: {status_counts.get('vorbereitet', 0)}",
        f"  Gesperrt: {status_counts.get('gesperrt', 0)}",
        f"  Platzhalter: {status_counts.get('platzhalter', 0)}",
        f"  Pruefung erforderlich: {status_counts.get('pruefung_erforderlich', 0)}",
        "",
        "5. FOLGEAUFTRAEGE",
        "-" * 40,
        "  [ ] UI-Schnittstellen (SI_UI_EINGANG_TUERSCHWELLE, SI_UI_MANDANTENAKTE) pruefen",
        "  [ ] Agenten-Schnittstelle (SI_AGENTEN_AUFTRAG) freigeben",
        "  [ ] Uebersetzungs-Schnittstelle (SI_UEBERSETZUNG_TERMINOLOGIE) nach Argos-Installation",
        "  [ ] Fundstellen-Schnittstelle (SI_FUNDSTELLEN_TEXTSTRUKTUR) entwickeln",
        "  [ ] DEEPL_API bleibt GESPERRT (Offline-Regel)",
        "",
        "=" * 70,
        "ENDE ANALYSEBERICHT",
        "=" * 70,
    ])

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    print(f"\nBericht geschrieben nach: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
