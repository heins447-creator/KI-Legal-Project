# -*- coding: utf-8 -*-
"""
CORE-02 - Pruefdatei
====================
Prueft die durch CORE-02 erstellten Register und Altbestandskarten:
1. JSON-Validitaet
2. Pflichtfelder gemaess Schema
3. Konsistenz zwischen Register und Altbestandskarten
4. Keine leeren Register (ausser update_register)

Ausgabe:
    - Pruefbericht auf stdout
    - Exit-Code 0 = OK, 1 = Fehler
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path("I:/KI_Legal_Project")
CORE_DIR = PROJECT_ROOT / "ALIN_Neustart_Core"
REGISTER_DIR = CORE_DIR / "01_Register"
ALTBESTAND_DIR = CORE_DIR / "07_Bestandsaufnahme_Altbestand"
REPORTS_DIR = CORE_DIR / "Reports"

ERRORS: List[str] = []
WARNINGS: List[str] = []


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def check_json_valid(path: Path) -> bool:
    try:
        load_json(path)
        return True
    except Exception as e:
        ERRORS.append(f"{path.name}: Ungueltiges JSON - {e}")
        return False


def check_register_fields(data: Dict, required_fields: List[str], name: str) -> None:
    for field in required_fields:
        if field not in data:
            ERRORS.append(f"{name}: Pflichtfeld '{field}' fehlt.")


def check_modulregister(data: Dict) -> None:
    check_register_fields(data, ["schema_version", "register_id", "letzte_aenderung", "eintraege"], "modulregister")
    for i, entry in enumerate(data.get("eintraege", [])):
        for field in ["modul_id", "modulname", "pfad", "version", "zweck", "status", "darf_aufgerufen_werden"]:
            if field not in entry:
                ERRORS.append(f"modulregister Eintrag {i}: '{field}' fehlt.")


def check_ressourcenregister(data: Dict) -> None:
    check_register_fields(data, ["schema_version", "register_id", "letzte_aenderung", "eintraege"], "ressourcenregister")
    for i, entry in enumerate(data.get("eintraege", [])):
        for field in ["resource_id", "typ", "status", "offline_verfuegbar", "online_erforderlich"]:
            if field not in entry:
                ERRORS.append(f"ressourcenregister Eintrag {i}: '{field}' fehlt.")


def check_toolregister(data: Dict) -> None:
    check_register_fields(data, ["schema_version", "register_id", "letzte_aenderung", "eintraege"], "toolregister")
    for i, entry in enumerate(data.get("eintraege", [])):
        for field in ["tool_id", "name", "kategorie", "installationsstatus", "darf_verwendet_werden"]:
            if field not in entry:
                ERRORS.append(f"toolregister Eintrag {i}: '{field}' fehlt.")


def check_skillregister(data: Dict) -> None:
    check_register_fields(data, ["schema_version", "register_id", "letzte_aenderung", "eintraege"], "skillregister")
    for i, entry in enumerate(data.get("eintraege", [])):
        for field in ["skill_id", "skillname", "zweck", "teststatus", "darf_bewerten", "darf_beweiswuerdigen"]:
            if field not in entry:
                ERRORS.append(f"skillregister Eintrag {i}: '{field}' fehlt.")
        if entry.get("darf_bewerten") is not False:
            ERRORS.append(f"skillregister Eintrag {i}: 'darf_bewerten' muss false sein.")
        if entry.get("darf_beweiswuerdigen") is not False:
            ERRORS.append(f"skillregister Eintrag {i}: 'darf_beweiswuerdigen' muss false sein.")


def check_quellenregister(data: Dict) -> None:
    check_register_fields(data, ["schema_version", "register_id", "letzte_aenderung", "eintraege"], "quellen_adapter_register")
    for i, entry in enumerate(data.get("eintraege", [])):
        for field in ["quelle_id", "quellentyp", "adapter", "darf_verwendet_werden"]:
            if field not in entry:
                ERRORS.append(f"quellen_adapter_register Eintrag {i}: '{field}' fehlt.")


def check_lizenzregister(data: Dict) -> None:
    check_register_fields(data, ["schema_version", "register_id", "letzte_aenderung", "eintraege"], "lizenzregister")
    for i, entry in enumerate(data.get("eintraege", [])):
        for field in ["komponente_id", "name", "lizenzname", "freigabestatus"]:
            if field not in entry:
                ERRORS.append(f"lizenzregister Eintrag {i}: '{field}' fehlt.")


def check_altbestand_konsistenz() -> None:
    """Prueft Konsistenz zwischen modulregister und altbestand_modulkarte."""
    mod_reg = load_json(REGISTER_DIR / "modulregister.json")
    mod_alt = load_json(ALTBESTAND_DIR / "altbestand_modulkarte.json")

    reg_ids = {e["modul_id"] for e in mod_reg.get("eintraege", [])}
    alt_ids = {e["modul_id"] for e in mod_alt.get("module", [])}

    if reg_ids != alt_ids:
        WARNINGS.append(f"Modulregister ({len(reg_ids)}) und Altbestandskarte ({len(alt_ids)}) haben unterschiedliche IDs.")


def main() -> int:
    print("=" * 70)
    print("CORE-02 - Pruefdatei")
    print("=" * 70)

    # 1. JSON-Validitaet
    print("\n[1/5] JSON-Validitaet pruefen...")
    files_to_check = list(REGISTER_DIR.glob("*.json")) + list(ALTBESTAND_DIR.glob("*.json"))
    for path in files_to_check:
        if check_json_valid(path):
            print(f"  OK {path.name}")
        else:
            print(f"  FEHLER {path.name}")

    # 2. Register-Felder
    print("\n[2/5] Register-Felder pruefen...")
    check_modulregister(load_json(REGISTER_DIR / "modulregister.json"))
    check_ressourcenregister(load_json(REGISTER_DIR / "ressourcenregister.json"))
    check_toolregister(load_json(REGISTER_DIR / "toolregister.json"))
    check_skillregister(load_json(REGISTER_DIR / "skillregister.json"))
    check_quellenregister(load_json(REGISTER_DIR / "quellen_adapter_register.json"))
    check_lizenzregister(load_json(REGISTER_DIR / "lizenzregister.json"))
    print("  Fertig.")

    # 3. Konsistenz
    print("\n[3/5] Konsistenz pruefen...")
    check_altbestand_konsistenz()
    print("  Fertig.")

    # 4. Leere Register
    print("\n[4/5] Leere Register pruefen...")
    for reg_file in REGISTER_DIR.glob("*.json"):
        if reg_file.name.endswith(".schema.json"):
            continue
        data = load_json(reg_file)
        if reg_file.name != "update_register.json" and not data.get("eintraege"):
            WARNINGS.append(f"{reg_file.name}: Register ist leer.")
    print("  Fertig.")

    # 5. Bericht
    print("\n[5/5] Ergebnis...")
    print("-" * 40)
    print(f"Fehler:   {len(ERRORS)}")
    print(f"Warnungen: {len(WARNINGS)}")

    if ERRORS:
        print("\nFEHLER:")
        for e in ERRORS:
            print(f"  X {e}")
    if WARNINGS:
        print("\nWARNUNGEN:")
        for w in WARNINGS:
            print(f"  ! {w}")

    # Pruefbericht schreiben
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    bericht_path = REPORTS_DIR / "ALIN_CORE02_PRUEFBERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-02 - Pruefbericht\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Fehler:    {len(ERRORS)}\n")
        f.write(f"Warnungen: {len(WARNINGS)}\n\n")
        if ERRORS:
            f.write("FEHLER:\n")
            for e in ERRORS:
                f.write(f"  X {e}\n")
        if WARNINGS:
            f.write("\nWARNUNGEN:\n")
            for w in WARNINGS:
                f.write(f"  ! {w}\n")
        f.write("\nENDE DES PRUEFBERICHTS\n")

    print(f"\nPruefbericht: {bericht_path}")

    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
