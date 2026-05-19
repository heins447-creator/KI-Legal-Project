# -*- coding: utf-8 -*-
"""
CORE-05 – Pruefdatei: Toolregister validieren
"""

import json
from pathlib import Path

CORE = Path("I:/KI_Legal_Project/ALIN_Neustart_Core")
REGISTER_DIR = CORE / "01_Register"
REPORTS_DIR = CORE / "Reports"

REQUIRED_FIELDS = [
    "tool_id", "name", "version", "kategorie", "pfad",
    "installationsstatus", "letzte_pruefung", "darf_verwendet_werden", "warnungen"
]

VALID_STATUS = ["installiert", "nicht_installiert", "veraltet", "unbekannt"]
VALID_KATEGORIEN = ["ocr", "pdf", "bildverarbeitung", "uebersetzung", "windows_app", "datenbank", "sicherheit", "sonstiges"]
VALID_VERSION_STATUS = ["bekannt", "unbekannt", "zu_pruefen"]
VALID_HEALTH_STATUS = ["ungeprueft", "bestanden", "fehlgeschlagen", "nicht_verfuegbar"]


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_register(data: dict, name: str) -> list:
    errors = []
    
    if data.get("schema_version") != "1.0.0":
        errors.append(f"{name}: schema_version nicht 1.0.0")
    if data.get("register_id") != "toolregister":
        errors.append(f"{name}: register_id nicht 'toolregister'")
    
    eintraege = data.get("eintraege", [])
    if not eintraege:
        errors.append(f"{name}: Keine Eintraege vorhanden")
    
    for idx, e in enumerate(eintraege):
        prefix = f"{name}[{idx}]"
        for field in REQUIRED_FIELDS:
            if field not in e:
                errors.append(f"{prefix}: Feld '{field}' fehlt")
        
        if e.get("kategorie") not in VALID_KATEGORIEN:
            errors.append(f"{prefix}: Ungueltige Kategorie '{e.get('kategorie')}'")
        if e.get("installationsstatus") not in VALID_STATUS:
            errors.append(f"{prefix}: Ungueltiger installationsstatus '{e.get('installationsstatus')}'")
        if e.get("version_status") and e.get("version_status") not in VALID_VERSION_STATUS:
            errors.append(f"{prefix}: Ungueltiger version_status '{e.get('version_status')}'")
        if e.get("healthcheck_status") and e.get("healthcheck_status") not in VALID_HEALTH_STATUS:
            errors.append(f"{prefix}: Ungueltiger healthcheck_status '{e.get('healthcheck_status')}'")
        
        if not isinstance(e.get("darf_verwendet_werden"), bool):
            errors.append(f"{prefix}: 'darf_verwendet_werden' muss boolean sein")
        if not isinstance(e.get("warnungen"), list):
            errors.append(f"{prefix}: 'warnungen' muss Liste sein")
    
    return errors


def main():
    print("=" * 70)
    print("CORE-05 – Toolregister Pruefung")
    print("=" * 70)
    
    path_01 = REGISTER_DIR / "toolregister.json"
    path_09 = CORE / "09_Toolbibliothek/00_Toolregister/ALIN_TOOLREGISTER.json"
    
    all_errors = []
    
    for path in [path_01, path_09]:
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
    bericht.append("CORE-05 TOOLREGISTER PRUEFBERICHT")
    bericht.append("=" * 70)
    bericht.append(f"Gepruefte Dateien: 2")
    bericht.append(f"Fehler: {len(all_errors)}")
    bericht.append("")
    if all_errors:
        bericht.append("Fehler:")
        for err in all_errors:
            bericht.append(f"  X {err}")
    else:
        bericht.append("Status: OK")
    bericht.append("=" * 70)
    
    bericht_path = REPORTS_DIR / "ALIN_CORE05_PRUEFBERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write("\n".join(bericht))
    print(f"\nBericht geschrieben nach: {bericht_path}")
    
    return 1 if all_errors else 0


if __name__ == "__main__":
    exit(main())
