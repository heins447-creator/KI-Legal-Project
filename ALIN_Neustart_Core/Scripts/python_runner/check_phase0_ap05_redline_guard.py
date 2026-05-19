#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.5."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from alin_core.redline_guard import evaluate_action, load_redlines, validate_redlines_structure


REQUIRED = [
    ROOT / ".alin" / "redlines.json",
    ROOT / ".alin" / "redlines.schema.json",
    ROOT / "Config" / "phase0_ap05_redline_guard_v1.json",
    ROOT / "Projektplanung" / "PHASE0_AP05_REDLINE_GUARD.md",
    ROOT / "Reports" / "PHASE0_AP05_REDLINE_GUARD_BERICHT.txt",
    ROOT / "Windows_App" / "Logs" / "PHASE0_AP05_REDLINE_GUARD_BERICHT.txt",
    ROOT / "alin_core" / "redline_guard.py",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_blocked(action: dict, expected_rule: str) -> None:
    decision = evaluate_action(action)
    if decision.allowed:
        fail(f"Aktion wurde nicht blockiert: {action}")
    if expected_rule not in {finding.rule_id for finding in decision.findings}:
        fail(f"Erwartete Regel fehlt: {expected_rule}")


def main() -> int:
    for path in REQUIRED:
        if not path.exists():
            fail(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")

    redlines = load_redlines()
    validate_redlines_structure(redlines)
    if len(redlines["rules"]) < 10:
        fail("Zu wenige rote Linien.")

    assert_blocked({"operation": "network_request", "note": "https://example.invalid"}, "RL003_INTERNET")
    assert_blocked({"operation": "database_write_without_migration"}, "RL005_DB_MIGRATION")
    assert_blocked({"operation": "copy_triage_to_case"}, "RL007_NO_TRIAGE_TO_CASE")
    assert_blocked({"operation": "delivery_without_tests"}, "RL009_TEST_REQUIRED")
    assert_blocked({"paths": ["I:/KI_Legal_Project/Outside/file.txt"]}, "RL001_SCOPE")

    allowed = evaluate_action({"operation": "write_report", "paths": ["Reports/local.txt"]})
    if not allowed.allowed:
        fail("Lokale harmlose Aktion wurde blockiert.")

    schema = json.loads((ROOT / ".alin" / "redlines.schema.json").read_text(encoding="utf-8"))
    if "rules" not in schema.get("required", []):
        fail("Schema verlangt rules nicht.")

    report = (ROOT / "Reports" / "PHASE0_AP05_REDLINE_GUARD_BERICHT.txt").read_text(encoding="utf-8")
    if "Verbotene Beispielaktion: blocked" not in report:
        fail("Bericht dokumentiert Blockade nicht.")

    print("PHASE 0, AP 0.5: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
