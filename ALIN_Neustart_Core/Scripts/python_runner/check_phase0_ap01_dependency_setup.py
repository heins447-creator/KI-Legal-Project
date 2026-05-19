#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.1."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
LOCKFILE = ROOT / "requirements.lock"
CONFIG = ROOT / "Config" / "phase0_ap01_dependency_policy_v1.json"
WHEELHOUSE_README = ROOT / "Wheelhouse" / "python" / "README.md"
DOC = ROOT / "Projektplanung" / "PHASE0_AP01_DEPENDENCY_SETUP.md"
REPORT = ROOT / "Reports" / "PHASE0_AP01_DEPENDENCY_SETUP_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP01_DEPENDENCY_SETUP_BERICHT.txt"


def fail(message: str) -> None:
    raise AssertionError(message)


def parse_lock() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in LOCKFILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" not in stripped:
            fail(f"Nicht gepinnte Lockfile-Zeile: {stripped}")
        name, version = stripped.split("==", 1)
        result[name.lower()] = version
    return result


def main() -> int:
    for path in [PYPROJECT, LOCKFILE, CONFIG, WHEELHOUSE_README, DOC, REPORT, LOG_REPORT]:
        if not path.exists():
            fail(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")
        if path.stat().st_size == 0:
            fail(f"Pflichtdatei ist leer: {path.relative_to(ROOT)}")

    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    locked = parse_lock()

    if pyproject["project"]["requires-python"] != ">=3.12,<3.13":
        fail("Python-Version im pyproject ist nicht auf 3.12 begrenzt.")

    if pyproject["tool"]["uv"]["offline"] is not True:
        fail("tool.uv.offline muss true sein.")

    direct_names = {
        dep.split("==", 1)[0].lower()
        for dep in pyproject["project"]["dependencies"]
    }
    required_direct = {"duckdb", "fastapi", "numpy", "uvicorn"}
    if direct_names != required_direct:
        fail(f"Direkte Abhaengigkeiten weichen ab: {sorted(direct_names)}")

    for name in required_direct:
        if name not in locked:
            fail(f"Direkte Abhaengigkeit fehlt im Lockfile: {name}")

    forbidden = {name.lower() for name in config["forbidden_dependency_names"]}
    forbidden_locked = forbidden.intersection(locked)
    if forbidden_locked:
        fail(f"Verbotene Abhaengigkeiten im Lockfile: {sorted(forbidden_locked)}")

    wheelhouse_text = WHEELHOUSE_README.read_text(encoding="utf-8")
    if "--offline" not in wheelhouse_text:
        fail("Wheelhouse-Dokumentation enthaelt keine Offline-Installationsregel.")

    report_text = REPORT.read_text(encoding="utf-8")
    if "keine Installation" not in report_text:
        fail("Bericht dokumentiert die Installationssperre nicht.")

    print("PHASE 0, AP 0.1: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
