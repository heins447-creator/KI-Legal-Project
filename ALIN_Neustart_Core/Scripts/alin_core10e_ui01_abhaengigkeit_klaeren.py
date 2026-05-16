#!/usr/bin/env python3
"""
CORE-10e – fehlende Abhaengigkeit ui01_anwaltsansicht klaeren
=============================================================
Auftrag:  Pruefen, ob check_ui01_anwaltsansicht_v1 auf ein existierendes
          Modul verweist, und ob die Abhaengigkeit korrekt benannt ist.
Harte Grenzen (AGENTS.md):
  - Keine UI bauen
  - Keine Altbestandsdateien aendern
  - Keine UI01 selbst reparieren
  - Keine Datenbankaenderung
  - Keine OCR
  - Keine Uebersetzung
  - Keine Ressourcen ergaenzen
  - Keine Schnittstellen bauen
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REGISTER_PFAD = Path("ALIN_Neustart_Core/01_Register/modulregister.json")
BERICHT_PFAD = Path("ALIN_Neustart_Core/Reports/ALIN_CORE10E_UI01_ABHAENGIGKEIT_BERICHT.txt")

def main():
    print("CORE-10e – UI01 Abhaengigkeit klaeren")
    print("=" * 60)

    if not REGISTER_PFAD.exists():
        print(f"FEHLER: {REGISTER_PFAD} nicht gefunden")
        return 1

    with open(REGISTER_PFAD, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Alle modul_ids sammeln
    modul_ids = {e["modul_id"] for e in data["eintraege"]}

    # check_ui01_anwaltsansicht_v1 finden
    check_modul = None
    for entry in data["eintraege"]:
        if entry["modul_id"] == "check_ui01_anwaltsansicht_v1":
            check_modul = entry
            break

    if not check_modul:
        print("FEHLER: check_ui01_anwaltsansicht_v1 nicht im Register gefunden")
        return 1

    abhaengigkeiten = check_modul.get("abhaengigkeiten", [])
    fehlende = []
    korrigierte = []

    for dep in abhaengigkeiten:
        if dep not in modul_ids:
            # Pruefe, ob _v1-Variante existiert
            dep_v1 = dep + "_v1"
            if dep_v1 in modul_ids:
                korrigierte.append({"alt": dep, "neu": dep_v1, "grund": "_v1-Suffix fehlte"})
            else:
                fehlende.append(dep)

    # Bericht erstellen
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bericht = []
    bericht.append("=" * 60)
    bericht.append("CORE-10e UI01 ABHAENGIGKEIT KLARUNG")
    bericht.append(f"Erstellt: {timestamp}")
    bericht.append("=" * 60)
    bericht.append("")
    bericht.append("Modul: check_ui01_anwaltsansicht_v1")
    bericht.append(f"Abhaengigkeiten: {abhaengigkeiten}")
    bericht.append("")

    if korrigierte:
        bericht.append("KORREKTUREN durchgefuehrt:")
        for k in korrigierte:
            bericht.append(f"  - {k['alt']} -> {k['neu']} ({k['grund']})")
        bericht.append("")

    if fehlende:
        bericht.append("FEHLENDE Abhaengigkeiten (nicht korrigierbar):")
        for f in fehlende:
            bericht.append(f"  - {f}")
        bericht.append("")
    else:
        bericht.append("Alle Abhaengigkeiten sind nun im Register vorhanden.")
        bericht.append("")

    bericht.append("=" * 60)
    bericht.append("ENDE BERICHT")
    bericht.append("=" * 60)

    bericht_text = "\n".join(bericht)
    BERICHT_PFAD.parent.mkdir(parents=True, exist_ok=True)
    with open(BERICHT_PFAD, "w", encoding="utf-8") as f:
        f.write(bericht_text)

    print(bericht_text)
    print(f"\nBericht geschrieben: {BERICHT_PFAD}")

    if fehlende:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
