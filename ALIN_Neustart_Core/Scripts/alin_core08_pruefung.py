# -*- coding: utf-8 -*-
"""
CORE-08 – Skillregister Prüfung
Prüft skillregister.json gegen Schema und Querschnittskonsistenz.
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
                print(f"  FEHLER: {name} fehlt Feld '{f}' in {eintrag.get('skill_id', '?')}")
                fehler += 1
    return fehler


def check_enum(data: Dict, field: str, allowed: Tuple[str, ...], name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        val = eintrag.get(field, "")
        if val and val not in allowed:
            print(f"  FEHLER: {name} ungueltiger Wert '{val}' fuer '{field}' in {eintrag.get('skill_id', '?')}")
            fehler += 1
    return fehler


def check_boolean(data: Dict, field: str, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        val = eintrag.get(field)
        if val is not None and not isinstance(val, bool):
            print(f"  FEHLER: {name} Feld '{field}' ist kein Boolean in {eintrag.get('skill_id', '?')}")
            fehler += 1
    return fehler


def check_unique_skill_ids(data: Dict, name: str) -> int:
    fehler = 0
    ids = [e.get("skill_id", "") for e in data.get("eintraege", [])]
    seen = set()
    for sid in ids:
        if sid in seen:
            print(f"  FEHLER: {name} doppelte skill_id '{sid}'")
            fehler += 1
        seen.add(sid)
    return fehler


def check_skill_id_pattern(data: Dict, name: str) -> int:
    fehler = 0
    pattern = re.compile(r"^[A-Z0-9_-]+$")
    for eintrag in data.get("eintraege", []):
        sid = eintrag.get("skill_id", "")
        if sid and not pattern.match(sid):
            print(f"  FEHLER: {name} skill_id '{sid}' entspricht nicht dem Pattern ^[A-Z0-9_-]+$")
            fehler += 1
    return fehler


def check_tool_linkages(data: Dict, tool_ids: set, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        for tid in eintrag.get("verwendete_tools", []):
            if tid and tid not in tool_ids:
                print(f"  WARNUNG: {name} Tool '{tid}' nicht im Toolregister in {eintrag.get('skill_id', '?')}")
                fehler += 1
    return fehler


def check_ressource_linkages(data: Dict, res_ids: set, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        for rid in eintrag.get("benoetigte_ressourcen", []):
            if rid and rid not in res_ids:
                print(f"  WARNUNG: {name} Ressource '{rid}' nicht im Ressourcenregister in {eintrag.get('skill_id', '?')}")
                fehler += 1
    return fehler


def check_quellen_linkages(data: Dict, quellen_ids: set, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        for qid in eintrag.get("benoetigte_quellen", []):
            if qid and qid not in quellen_ids:
                print(f"  WARNUNG: {name} Quelle '{qid}' nicht im Quellenregister in {eintrag.get('skill_id', '?')}")
                fehler += 1
    return fehler


def main() -> int:
    root = Path("I:/KI_Legal_Project")
    core = root / "ALIN_Neustart_Core"

    reg_path = core / "01_Register" / "skillregister.json"
    toolreg_path = core / "01_Register" / "toolregister.json"
    resreg_path = core / "01_Register" / "ressourcenregister.json"
    quellenreg_path = core / "01_Register" / "quellen_adapter_register.json"
    bericht_path = core / "Reports" / "ALIN_CORE08_PRUEFBERICHT.txt"

    print("=" * 70)
    print("CORE-08 – Skillregister Pruefung")
    print("=" * 70)

    fehler = 0

    # JSON gueltig?
    if not check_json_valid(reg_path):
        fehler += 1

    reg = load_json(reg_path)
    toolreg = load_json(toolreg_path)
    resreg = load_json(resreg_path)
    quellenreg = load_json(quellenreg_path)

    tool_ids = {t["tool_id"] for t in toolreg.get("eintraege", [])}
    res_ids = {r["resource_id"] for r in resreg.get("eintraege", [])}
    quellen_ids = {q["quelle_id"] for q in quellenreg.get("eintraege", [])}

    required = [
        "skill_id", "skillname", "zweck", "eingabe", "ausgabe",
        "modellabhaengigkeit", "fallback", "teststatus",
        "darf_bewerten", "darf_beweiswuerdigen", "warnungen"
    ]

    fehler += check_register_fields(reg, required, "skillregister.json")
    fehler += check_enum(reg, "teststatus", ("geprueft", "testbar", "ungeprueft", "gesperrt"), "skillregister.json")
    fehler += check_boolean(reg, "darf_bewerten", "skillregister.json")
    fehler += check_boolean(reg, "darf_beweiswuerdigen", "skillregister.json")
    fehler += check_unique_skill_ids(reg, "skillregister.json")
    fehler += check_skill_id_pattern(reg, "skillregister.json")
    fehler += check_tool_linkages(reg, tool_ids, "skillregister.json")
    fehler += check_ressource_linkages(reg, res_ids, "skillregister.json")
    fehler += check_quellen_linkages(reg, quellen_ids, "skillregister.json")

    # Zusaetzliche Felder pruefen
    fehler += check_boolean(reg, "offline_moeglich", "skillregister.json")
    fehler += check_boolean(reg, "online_erforderlich", "skillregister.json")
    fehler += check_boolean(reg, "darf_rechtsbewertung", "skillregister.json")
    fehler += check_boolean(reg, "darf_stammdaten_aendern", "skillregister.json")
    fehler += check_boolean(reg, "darf_originale_veraendern", "skillregister.json")

    print(f"\nValidierung: {fehler} Fehler")

    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(f"CORE-08 Pruefbericht\n")
        f.write(f"Fehler: {fehler}\n")
        f.write(f"Eintraege: {len(reg.get('eintraege', []))}\n")

    print(f"Bericht geschrieben nach: {bericht_path}")
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
