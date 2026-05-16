# -*- coding: utf-8 -*-
"""
CORE-06 – Ressourcenregister Prüfung
Prüft ressourcenregister.json gegen Schema und Querschnittskonsistenz.
"""

import json
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
                print(f"  FEHLER: {name} fehlt Feld '{f}' in {eintrag.get('resource_id', '?')}")
                fehler += 1
    return fehler


def check_enum(data: Dict, field: str, allowed: Tuple[str, ...], name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        val = eintrag.get(field, "")
        if val and val not in allowed:
            print(f"  FEHLER: {name} ungueltiger Wert '{val}' fuer '{field}' in {eintrag.get('resource_id', '?')}")
            fehler += 1
    return fehler


def check_boolean(data: Dict, field: str, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        val = eintrag.get(field)
        if val is not None and not isinstance(val, bool):
            print(f"  FEHLER: {name} Feld '{field}' ist kein Boolean in {eintrag.get('resource_id', '?')}")
            fehler += 1
    return fehler


def check_tool_linkages(data: Dict, tool_ids: set, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        tid = eintrag.get("tool_id", "")
        if tid and tid not in tool_ids:
            print(f"  WARNUNG: {name} Tool '{tid}' nicht im Toolregister in {eintrag.get('resource_id', '?')}")
            fehler += 1
    return fehler


def check_update_linkages(data: Dict, upd_ids: set, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        uid = eintrag.get("update_id", "")
        if uid and uid not in upd_ids:
            print(f"  WARNUNG: {name} Update '{uid}' nicht im Update-Register in {eintrag.get('resource_id', '?')}")
            fehler += 1
    return fehler


def check_lizenz_linkages(data: Dict, liz_ids: set, name: str) -> int:
    fehler = 0
    for eintrag in data.get("eintraege", []):
        lid = eintrag.get("lizenz_id", "")
        if lid and lid not in liz_ids:
            print(f"  WARNUNG: {name} Lizenz '{lid}' nicht im Lizenzregister in {eintrag.get('resource_id', '?')}")
            fehler += 1
    return fehler


def main() -> int:
    root = Path("I:/KI_Legal_Project")
    core = root / "ALIN_Neustart_Core"

    reg_path = core / "01_Register" / "ressourcenregister.json"
    toolreg_path = core / "01_Register" / "toolregister.json"
    upd_path = core / "01_Register" / "update_register.json"
    liz_path = core / "01_Register" / "lizenzregister.json"
    bericht_path = core / "Reports" / "ALIN_CORE06_PRUEFBERICHT.txt"

    print("=" * 70)
    print("CORE-06 – Ressourcenregister Pruefung")
    print("=" * 70)

    fehler = 0

    # JSON gueltig?
    if not check_json_valid(reg_path):
        fehler += 1

    reg = load_json(reg_path)
    toolreg = load_json(toolreg_path)
    updreg = load_json(upd_path)
    lizreg = load_json(liz_path)

    tool_ids = {t["tool_id"] for t in toolreg.get("eintraege", [])}
    upd_ids = {u["update_id"] for u in updreg.get("eintraege", [])}
    liz_ids = {l["komponente_id"] for l in lizreg.get("eintraege", [])}

    required = [
        "resource_id", "typ", "sprache", "land", "rechtsraum",
        "rechtsgebiet", "dokumenttyp", "pfad", "status",
        "offline_verfuegbar", "online_erforderlich",
        "fallback", "letzte_pruefung", "warnungen"
    ]

    fehler += check_register_fields(reg, required, "ressourcenregister.json")
    fehler += check_enum(reg, "typ", (
        "ocr_sprachpaket", "uebersetzungsmodell", "terminologie",
        "schriftart", "vorlage", "quellenregister", "adapter",
        "windows_app_ressource", "ui_hilfe", "sicherheitsressource", "sonstiges"
    ), "ressourcenregister.json")
    fehler += check_enum(reg, "status", ("freigegeben", "testbar", "veraltet", "gesperrt", "fehlt"), "ressourcenregister.json")
    fehler += check_enum(reg, "pruefstatus", ("geprueft", "ungeprueft", "fehlerhaft", "nicht_pruefbar"), "ressourcenregister.json")
    fehler += check_enum(reg, "vorhanden_ja_nein_unbekannt", ("ja", "nein", "unbekannt"), "ressourcenregister.json")
    fehler += check_boolean(reg, "offline_verfuegbar", "ressourcenregister.json")
    fehler += check_boolean(reg, "online_erforderlich", "ressourcenregister.json")
    fehler += check_boolean(reg, "darf_von_modulen_verwendet_werden", "ressourcenregister.json")
    fehler += check_tool_linkages(reg, tool_ids, "ressourcenregister.json")
    fehler += check_update_linkages(reg, upd_ids, "ressourcenregister.json")
    fehler += check_lizenz_linkages(reg, liz_ids, "ressourcenregister.json")

    print(f"\nValidierung: {fehler} Fehler")

    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(f"CORE-06 Pruefbericht\n")
        f.write(f"Fehler: {fehler}\n")
        f.write(f"Eintraege: {len(reg.get('eintraege', []))}\n")

    print(f"Bericht geschrieben nach: {bericht_path}")
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
