# -*- coding: utf-8 -*-
"""
CORE-07 – Quellen- und Adapterregister Prüfung
Prüft quellen_adapter_register.json gegen Schema und Querschnittskonsistenz.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_json_valid(path: Path) -> bool:
    try:
        load_json(path)
        return True
    except json.JSONDecodeError as e:
        print(f"  FEHLER: JSON ungueltig in {path}: {e}")
        return False


def check_register_fields(data: Dict, required_fields: List[str], name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        for f in required_fields:
            if f not in eintrag:
                print(f"  FEHLER: {name} fehlt Feld '{f}' in {eintrag.get('quelle_id', '?')}")
                fehler += 1
    return fehler


def check_enum(data: Dict, field: str, allowed: Tuple[str, ...], name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        val = eintrag.get(field, "")
        if val and val not in allowed:
            print(f"  FEHLER: {name} ungueltiger Wert '{val}' fuer '{field}' in {eintrag.get('quelle_id', '?')}")
            fehler += 1
    return fehler


def check_boolean(data: Dict, field: str, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        val = eintrag.get(field)
        if val is not None and not isinstance(val, bool):
            print(f"  FEHLER: {name} Feld '{field}' ist kein Boolean in {eintrag.get('quelle_id', '?')}")
            fehler += 1
    return fehler


def check_unique_quelle_ids(data: Dict, name: str) -> int:
    fehler = 0
    ids = [e.get("quelle_id", "") for e in data.get("eintraege", [])]
    seen = set()
    for qid in ids:
        if qid in seen:
            print(f"  FEHLER: {name} doppelte quelle_id '{qid}'")
            fehler += 1
        seen.add(qid)
    return fehler


def check_quelle_id_pattern(data: Dict, name: str) -> int:
    fehler = 0
    pattern = re.compile(r"^[A-Z0-9_-]+$")
    for eintrag in data.get("eintraege", []):
        qid = eintrag.get("quelle_id", "")
        if qid and not pattern.match(qid):
            print(f"  FEHLER: {name} quelle_id '{qid}' entspricht nicht dem Pattern ^[A-Z0-9_-]+$")
            fehler += 1
    return fehler


def check_adapter_pattern(data: Dict, name: str) -> int:
    fehler = 0
    pattern = re.compile(r"^[A-Za-z0-9_]+$")
    for eintrag in data.get("eintraege", []):
        adapter = eintrag.get("adapter", "")
        if adapter and not pattern.match(adapter):
            print(f"  FEHLER: {name} adapter '{adapter}' entspricht nicht dem Pattern ^[A-Za-z0-9_]+$ in {eintrag.get('quelle_id', '?')}")
            fehler += 1
    return fehler


def main() -> int:
    root = Path("I:/KI_Legal_Project")
    core = root / "ALIN_Neustart_Core"

    reg_path = core / "01_Register" / "quellen_adapter_register.json"
    bericht_path = core / "Reports" / "ALIN_CORE07_PRUEFBERICHT.txt"

    print("=" * 70)
    print("CORE-07 – Quellen- und Adapterregister Pruefung")
    print("=" * 70)

    fehler = 0

    # JSON gueltig?
    if not check_json_valid(reg_path):
        fehler += 1

    reg = load_json(reg_path)

    required = [
        "quelle_id", "quellentyp", "land", "rechtsgebiet", "sprache",
        "adapter", "online_status", "offline_cache_status", "dry_run_status",
        "letzter_healthcheck", "darf_verwendet_werden", "warnungen"
    ]

    fehler += check_register_fields(reg, required, "quellen_adapter_register.json")
    fehler += check_enum(reg, "quellentyp", (
        "gesetz", "verordnung", "gerichtsentscheidung", "fachliteratur", "datenbank", "sonstiges"
    ), "quellen_adapter_register.json")
    fehler += check_enum(reg, "online_status", (
        "verfuegbar", "eingeschraenkt", "nicht_verfuegbar", "unbekannt"
    ), "quellen_adapter_register.json")
    fehler += check_enum(reg, "offline_cache_status", (
        "aktuell", "veraltet", "fehlt", "nicht_vorgesehen"
    ), "quellen_adapter_register.json")
    fehler += check_enum(reg, "dry_run_status", (
        "moeglich", "nicht_moeglich", "ungetestet"
    ), "quellen_adapter_register.json")
    fehler += check_boolean(reg, "darf_verwendet_werden", "quellen_adapter_register.json")
    fehler += check_unique_quelle_ids(reg, "quellen_adapter_register.json")
    fehler += check_quelle_id_pattern(reg, "quellen_adapter_register.json")
    fehler += check_adapter_pattern(reg, "quellen_adapter_register.json")

    print(f"\nValidierung: {fehler} Fehler")

    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(f"CORE-07 Pruefbericht\n")
        f.write(f"Fehler: {fehler}\n")
        f.write(f"Eintraege: {len(reg.get('eintraege', []))}\n")

    print(f"Bericht geschrieben nach: {bericht_path}")
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
