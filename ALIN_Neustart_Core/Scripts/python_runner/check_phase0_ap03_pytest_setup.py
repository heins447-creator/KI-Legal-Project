#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.3 ohne pytest-Abhaengigkeit."""

from __future__ import annotations

import importlib.util
import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
CONFIG = ROOT / "Config" / "phase0_ap03_pytest_setup_v1.json"
TESTS_DIR = ROOT / "tests"
DOC = ROOT / "Projektplanung" / "PHASE0_AP03_PYTEST_SETUP.md"
REPORT = ROOT / "Reports" / "PHASE0_AP03_PYTEST_SETUP_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP03_PYTEST_SETUP_BERICHT.txt"


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    for path in [PYPROJECT, CONFIG, TESTS_DIR / "README.md", DOC, REPORT, LOG_REPORT]:
        if not path.exists():
            fail(f"Pflichtpfad fehlt: {path.relative_to(ROOT)}")

    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    pytest_config = pyproject.get("tool", {}).get("pytest", {}).get("ini_options")
    if not pytest_config:
        fail("pytest-Konfiguration fehlt in pyproject.toml.")
    if pytest_config.get("testpaths") != ["tests"]:
        fail("pytest testpaths ist nicht auf tests gesetzt.")
    if "--strict-config" not in pytest_config.get("addopts", []):
        fail("pytest strict-config fehlt.")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config["pytest"]["install_automatically"] is not False:
        fail("pytest darf nicht automatisch installiert werden.")

    test_files = sorted(TESTS_DIR.glob("test_*.py"))
    if len(test_files) < 2:
        fail("Zu wenige pytest-kompatible Testdateien.")

    forbidden_texts = ["openai", "requests.get(", "http://", "https://"]
    for path in test_files:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in forbidden_texts:
            if forbidden in text:
                fail(f"Verbotenes Testmuster in {path.relative_to(ROOT)}: {forbidden}")

    pytest_status = "vorhanden" if importlib.util.find_spec("pytest") else "nicht installiert"
    report = REPORT.read_text(encoding="utf-8")
    if pytest_status == "nicht installiert" and "pytest verfuegbar: nein" not in report:
        fail("Bericht dokumentiert fehlendes pytest nicht korrekt.")

    print("PHASE 0, AP 0.3: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
