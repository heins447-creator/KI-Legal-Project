#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.4."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from alin_core.logging_config import configure_json_logging, get_default_log_dir, log_event


CONFIG = ROOT / "Config" / "phase0_ap04_logging_v1.json"
DOC = ROOT / "Projektplanung" / "PHASE0_AP04_LOGGING_SETUP.md"
REPORT = ROOT / "Reports" / "PHASE0_AP04_LOGGING_SETUP_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP04_LOGGING_SETUP_BERICHT.txt"


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    for path in [CONFIG, DOC, REPORT, LOG_REPORT, ROOT / "alin_core" / "logging_config.py"]:
        if not path.exists():
            fail(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config["logging"]["format"] != "json_lines":
        fail("Logging-Format muss json_lines sein.")
    if config["privacy"]["internet_allowed"] is not False:
        fail("Logging darf keinen Internetzugriff erlauben.")

    default_dir = get_default_log_dir()
    if "ALIN" not in str(default_dir) or "Logs" not in str(default_dir):
        fail(f"Standard-Logpfad unerwartet: {default_dir}")

    test_dir = ROOT / "Windows_App" / "Logs" / "logging_check"
    logger, log_path = configure_json_logging("alin.phase0.ap04.check", log_dir=test_dir)
    log_event(
        logger,
        event="phase0_ap04_check",
        message="Check",
        context={"synthetic": True},
        level=logging.WARNING,
    )
    for handler in logger.handlers:
        handler.flush()

    line = log_path.read_text(encoding="utf-8").splitlines()[0]
    payload = json.loads(line)
    for field in ["timestamp", "level", "logger", "message", "module", "event", "context"]:
        if field not in payload:
            fail(f"JSON-Logfeld fehlt: {field}")
    if payload["level"] != "WARNING":
        fail("Log-Level wurde nicht korrekt geschrieben.")
    if payload["context"].get("synthetic") is not True:
        fail("Kontext wurde nicht korrekt geschrieben.")

    report = REPORT.read_text(encoding="utf-8")
    if "Zentrale JSON-Logging-Komponente" not in report:
        fail("Bericht dokumentiert Ergebnis nicht.")

    print("PHASE 0, AP 0.4: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
