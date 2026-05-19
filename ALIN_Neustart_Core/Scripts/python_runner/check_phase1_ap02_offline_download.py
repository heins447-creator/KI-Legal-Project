"""
Check-Skript fuer AP 1.2: Prueft ob alle 6 Tools im SHA256-Manifest vorhanden sind.

Aufruf: python check_phase1_ap02_offline_download.py
Exitcode 0 = OK, 1 = Fehler
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase1_ap02_offline_download_v1.json"
MANIFEST = ROOT / "09_Toolbibliothek" / "04_Hashes" / "SHA256_MANIFEST.csv"

ERWARTETE_TOOLS = {"PADDLEOCR", "PYHANKO", "MSOFFCRYPTO", "CLAMAV", "OLLAMA", "ARGOS_TRANSLATE"}


def main():
    fehler = []

    if not CONFIG_PATH.exists():
        print(f"FEHLER: Config nicht gefunden: {CONFIG_PATH}")
        sys.exit(1)

    if not MANIFEST.exists():
        print(f"FEHLER: SHA256-Manifest nicht gefunden: {MANIFEST}")
        print("Hinweis: phase1_ap02_offline_download.py ausfuehren.")
        sys.exit(1)

    with open(MANIFEST, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        eintraege = {row["tool_id"]: row for row in reader}

    fehlende = ERWARTETE_TOOLS - set(eintraege.keys())
    if fehlende:
        fehler.append(f"Fehlende Tools im Manifest: {fehlende}")

    for tool_id, eintrag in eintraege.items():
        if tool_id not in ERWARTETE_TOOLS:
            continue
        if not eintrag.get("sha256") or eintrag["sha256"] == "dry-run":
            fehler.append(f"{tool_id}: SHA-256 fehlt oder ist Platzhalter")
        if not eintrag.get("datei"):
            fehler.append(f"{tool_id}: Datei-Pfad fehlt")

    if fehler:
        print("AP 1.2 NICHT BESTANDEN:")
        for f in fehler:
            print(f"  - {f}")
        sys.exit(1)

    print(f"AP 1.2 OK: {len(ERWARTETE_TOOLS)} Tools im Manifest mit SHA-256.")
    for tool_id in sorted(ERWARTETE_TOOLS):
        e = eintraege[tool_id]
        print(f"  {tool_id}: {e['sha256'][:16]}... ({e['datei']})")


if __name__ == "__main__":
    main()
