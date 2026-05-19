# -*- coding: utf-8 -*-
"""
CORE-04 – Prüfdatei: Update-Register validieren
"""

import json
from pathlib import Path

CORE = Path("I:/KI_Legal_Project/ALIN_Neustart_Core")
REGISTER_DIR = CORE / "01_Register"
UPDATE_DIR = CORE / "10_Update_Ueberwachung/00_Update_Register"
REPORTS_DIR = CORE / "Reports"

REQUIRED_FIELDS = [
    "update_id", "komponente_id", "aktuelle_version", "verfuegbare_version",
    "quelle", "lizenz", "hash", "pruefstatus", "automatische_pruefung",
    "automatische_ersetzung", "rollback_moeglich", "freigabeprotokoll", "warnungen"
]

VALID_STATUS = ["geprueft", "testbar", "ungeprueft", "gesperrt", "zurueckgesetzt"]


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_register(data: dict, name: str) -> list:
    errors = []
    
    if data.get("schema_version") != "1.0.0":
        errors.append(f"{name}: schema_version nicht 1.0.0")
    if data.get("register_id") != "update_register":
        errors.append(f"{name}: register_id nicht 'update_register'")
    
    eintraege = data.get("eintraege", [])
    if not eintraege:
        errors.append(f"{name}: Keine Eintraege vorhanden")
    
    for idx, e in enumerate(eintraege):
        prefix = f"{name}[{idx}]"
        for field in REQUIRED_FIELDS:
            if field not in e:
                errors.append(f"{prefix}: Feld '{field}' fehlt")
        
        if e.get("pruefstatus") not in VALID_STATUS:
            errors.append(f"{prefix}: Ungueltiger pruefstatus '{e.get('pruefstatus')}'")
        
        if not isinstance(e.get("automatische_pruefung"), bool):
            errors.append(f"{prefix}: 'automatische_pruefung' muss boolean sein")
        if not isinstance(e.get("automatische_ersetzung"), bool):
            errors.append(f"{prefix}: 'automatische_ersetzung' muss boolean sein")
        if not isinstance(e.get("rollback_moeglich"), bool):
            errors.append(f"{prefix}: 'rollback_moeglich' muss boolean sein")
        
        if not isinstance(e.get("freigabeprotokoll"), list):
            errors.append(f"{prefix}: 'freigabeprotokoll' muss Liste sein")
        if not isinstance(e.get("warnungen"), list):
            errors.append(f"{prefix}: 'warnungen' muss Liste sein")
    
    return errors


def main():
    print("=" * 70)
    print("CORE-04 – Update-Register Prüfung")
    print("=" * 70)
    
    path_01 = REGISTER_DIR / "update_register.json"
    path_10 = UPDATE_DIR / "ALIN_UPDATE_REGISTER.json"
    
    all_errors = []
    
    for path in [path_01, path_10]:
        if not path.exists():
            all_errors.append(f"Datei nicht gefunden: {path}")
            continue
        
        try:
            data = load_json(path)
        except json.JSONDecodeError as e:
            all_errors.append(f"JSON-Fehler in {path}: {e}")
            continue
        
        errors = validate_register(data, path.name)
        all_errors.extend(errors)
        
        print(f"{path.name}: {len(data.get('eintraege', []))} Eintraege")
    
    print(f"\nValidierung: {len(all_errors)} Fehler")
    for err in all_errors:
        print(f"  X {err}")
    
    # Bericht schreiben
    bericht = []
    bericht.append("=" * 70)
    bericht.append("CORE-04 UPDATE-REGISTER PRÜFBERICHT")
    bericht.append("=" * 70)
    bericht.append(f"Geprüfte Dateien: 2")
    bericht.append(f"Fehler: {len(all_errors)}")
    bericht.append("")
    if all_errors:
        bericht.append("Fehler:")
        for err in all_errors:
            bericht.append(f"  X {err}")
    else:
        bericht.append("Status: OK")
    bericht.append("=" * 70)
    
    bericht_path = REPORTS_DIR / "ALIN_CORE04_PRUEFBERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write("\n".join(bericht))
    print(f"\nBericht geschrieben nach: {bericht_path}")
    
    return 1 if all_errors else 0


if __name__ == "__main__":
    exit(main())
