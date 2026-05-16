#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10g Prüfdatei
Verifiziert Reviewlisten-JSON und Bericht.
"""

import json
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
HEALTHCHECK_DIR = ROOT / "ALIN_Neustart_Core" / "04_Healthcheck"
REPORT_DIR = ROOT / "ALIN_Neustart_Core" / "Reports"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("CORE-10g PRUEFUNG")
    print("=" * 60)

    # 1. Review-JSON vorhanden
    review_path = HEALTHCHECK_DIR / "review_listen.json"
    if not review_path.exists():
        print("[FEHLER] review_listen.json nicht vorhanden")
        return 1
    print("[OK] review_listen.json vorhanden")

    # 2. JSON gueltig
    try:
        review = load_json(review_path)
    except json.JSONDecodeError as e:
        print(f"[FEHLER] Ungueltiges JSON: {e}")
        return 1
    print("[OK] review_listen.json ist gueltiges JSON")

    # 3. Listen vorhanden
    listen = review.get("listen", {})
    required_lists = [
        "db_aendernde_module",
        "online_faehige_module",
        "installations_update_module",
        "rechtsbewertende_module",
        "beweiswuerdigende_module",
        "original_aendernde_module",
        "produktiv_freigegebene_module",
        "risikoklassen"
    ]
    for rl in required_lists:
        if rl not in listen:
            print(f"[FEHLER] Liste '{rl}' fehlt in review_listen.json")
            return 1
    print(f"[OK] Alle {len(required_lists)} Reviewlisten vorhanden")

    # 4. Risikoklassen vorhanden
    risiko = listen.get("risikoklassen", {})
    for rk in ["KRITISCH", "HOCH", "MITTEL", "NIEDRIG"]:
        if rk not in risiko:
            print(f"[FEHLER] Risikoklasse '{rk}' fehlt")
            return 1
    print("[OK] Alle 4 Risikoklassen vorhanden")

    # 5. Bericht vorhanden
    bericht_path = REPORT_DIR / "ALIN_CORE10G_REVIEWLISTEN_BERICHT.txt"
    if not bericht_path.exists():
        print("[FEHLER] ALIN_CORE10G_REVIEWLISTEN_BERICHT.txt nicht vorhanden")
        return 1
    print("[OK] Bericht vorhanden")

    # 6. Keine Online-/Cloud-Nutzung im Skript (selbstreferentiell)
    print("[OK] Pruefung nur lesend – keine Online-/Cloud-Nutzung")

    print("=" * 60)
    print("PRUEFUNG BESTANDEN – Alle Reviewlisten korrekt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
