#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10b Prüfdatei
Verifiziert, dass alle referenzierten Ressourcen im Ressourcenregister existieren
und Tool-/Update-/Lizenz-Verknüpfungen korrekt sind.
"""

import json
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("CORE-10b PRUEFUNG")
    print("=" * 60)

    ressourcenregister = load_json(REGISTER_DIR / "ressourcenregister.json")
    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    toolregister = load_json(REGISTER_DIR / "toolregister.json")
    update_register = load_json(REGISTER_DIR / "update_register.json")
    lizenzregister = load_json(REGISTER_DIR / "lizenzregister.json")

    register_ids = {e.get("resource_id") for e in ressourcenregister.get("eintraege", [])}
    tool_ids = {e.get("tool_id") for e in toolregister.get("eintraege", [])}
    update_ids = {e.get("update_id") for e in update_register.get("eintraege", [])}
    lizenz_ids = {e.get("komponente_id") for e in lizenzregister.get("eintraege", [])}

    fehler = []

    # Prüfung 1: Alle in Modulen referenzierten Ressourcen existieren im Register
    modul_ressourcen = set()
    for modul in modulregister.get("eintraege", []):
        for res in modul.get("benoetigte_ressourcen", []):
            modul_ressourcen.add(res)

    fehlende_im_register = modul_ressourcen - register_ids
    if fehlende_im_register:
        for res in sorted(fehlende_im_register):
            fehler.append(f"FEHLT: Ressource '{res}' wird von Modulen referenziert, fehlt aber im Ressourcenregister")
    else:
        print("[OK] Alle von Modulen referenzierten Ressourcen existieren im Register")

    # Prüfung 2: TESSERACT Tool-Verknüpfung
    if "TESSERACT" not in tool_ids:
        fehler.append("FEHLT: Tool 'TESSERACT' nicht im Toolregister")
    else:
        print("[OK] Tool TESSERACT im Toolregister vorhanden")

    if "UPD_TESSERACT" not in update_ids:
        fehler.append("FEHLT: Update 'UPD_TESSERACT' nicht im Update-Register")
    else:
        print("[OK] Update UPD_TESSERACT im Update-Register vorhanden")

    if "TESSERACT" not in lizenz_ids:
        fehler.append("FEHLT: Lizenz 'TESSERACT' nicht im Lizenzregister")
    else:
        print("[OK] Lizenz TESSERACT im Lizenzregister vorhanden")

    # Prüfung 3: ARGOS_TRANSLATE Tool-Verknüpfung
    if "ARGOS_TRANSLATE" not in tool_ids:
        fehler.append("FEHLT: Tool 'ARGOS_TRANSLATE' nicht im Toolregister")
    else:
        print("[OK] Tool ARGOS_TRANSLATE im Toolregister vorhanden")

    if "UPD_ARGOS" not in update_ids:
        fehler.append("FEHLT: Update 'UPD_ARGOS' nicht im Update-Register")
    else:
        print("[OK] Update UPD_ARGOS im Update-Register vorhanden")

    if "ARGOS" not in lizenz_ids:
        fehler.append("FEHLT: Lizenz 'ARGOS' nicht im Lizenzregister")
    else:
        print("[OK] Lizenz ARGOS im Lizenzregister vorhanden")

    # Prüfung 4: ARGOS_TRANSLATE hat update_id UPD_ARGOS (nicht leer)
    for tool in toolregister.get("eintraege", []):
        if tool.get("tool_id") == "ARGOS_TRANSLATE":
            if tool.get("update_id") != "UPD_ARGOS":
                fehler.append(f"FEHLER: ARGOS_TRANSLATE update_id='{tool.get('update_id')}' erwartet 'UPD_ARGOS'")
            else:
                print("[OK] ARGOS_TRANSLATE update_id korrekt auf 'UPD_ARGOS' gesetzt")
            break

    print("=" * 60)
    if fehler:
        print(f"PRUEFUNG FEHLGESCHLAGEN – {len(fehler)} Fehler:")
        for f in fehler:
            print(f"  {f}")
        return 1
    else:
        print("PRUEFUNG BESTANDEN – Keine Fehler")
        return 0


if __name__ == "__main__":
    sys.exit(main())
