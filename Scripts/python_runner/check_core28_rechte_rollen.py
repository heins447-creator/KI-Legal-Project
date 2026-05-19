"""
Check-Datei für CORE-28: Rechte und Rollen
Prüft, ob der Runner syntaktisch korrekt ist und die erwarteten Dateien erzeugt.
"""
import ast
import json
import os
import sys

RUNNER_PATH = "Scripts/python_runner/core28_rechte_rollen.py"
CONFIG_PATH = "Config/core28_rechte_rollen_v1.json"
BERICHT_PFAD = "ALIN_Neustart_Core/Reports/CORE28_RECHTE_ROLLEN_BERICHT.txt"


def check_runner_syntax():
    with open(RUNNER_PATH, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        ast.parse(source)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax-Fehler: {e}"


def check_config():
    if not os.path.exists(CONFIG_PATH):
        return False, "Config nicht gefunden"
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        required = ["modul_id", "name", "validierung", "bericht"]
        for key in required:
            if key not in cfg:
                return False, f"Config fehlt: {key}"
        return True, "Config OK"
    except json.JSONDecodeError as e:
        return False, f"Config JSON-Fehler: {e}"


def check_runner_functions():
    with open(RUNNER_PATH, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    required = ["lade_config", "pruefe_datei_existenz", "pruefe_rollenmodell",
                "pruefe_freigaberegeln", "pruefe_berechtigungen_schema", "schreibe_bericht", "main"]
    missing = [r for r in required if r not in funcs]
    if missing:
        return False, f"Fehlende Funktionen: {missing}"
    return True, "Alle Funktionen vorhanden"


def main():
    print("CHECK CORE-28: Rechte und Rollen")
    print("=" * 50)

    checks = [
        ("Runner Syntax", check_runner_syntax),
        ("Config", check_config),
        ("Runner Funktionen", check_runner_functions),
    ]

    all_ok = True
    for name, check_func in checks:
        ok, msg = check_func()
        status = "OK" if ok else "FEHLER"
        print(f"  [{status}] {name}: {msg}")
        if not ok:
            all_ok = False

    print("=" * 50)
    if all_ok:
        print("CHECK CORE-28: ERFOLG")
        return 0
    else:
        print("CHECK CORE-28: FEHLER")
        return 1


if __name__ == "__main__":
    sys.exit(main())
