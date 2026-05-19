#!/usr/bin/env python3
"""Phase 0, AP 0.4: JSON-Logging einrichten und protokollieren."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from alin_core.logging_config import configure_json_logging, get_default_log_dir, log_event


CONFIG_PATH = ROOT / "Config" / "phase0_ap04_logging_v1.json"
REPORT_PATH = ROOT / "Reports" / "PHASE0_AP04_LOGGING_SETUP_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP04_LOGGING_SETUP_BERICHT.txt"


def render_report(config: dict, smoke_log_path: Path, parsed_event: dict) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.4 JSON-LOGGING BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        f"Standard-Logpfad: {get_default_log_dir()}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "Zentrale JSON-Logging-Komponente ist angelegt.",
        "Smoke-Log wurde synthetisch geschrieben und als JSON gelesen.",
        "",
        "SMOKE-TEST",
        "-" * 70,
        f"Logdatei: {smoke_log_path}",
        f"Event: {parsed_event.get('event')}",
        f"Level: {parsed_event.get('level')}",
        "",
        "SPERREN",
        "-" * 70,
        f"Echte Mandantendaten erlaubt: {config['privacy']['real_client_data_allowed']}",
        f"Internet erlaubt: {config['privacy']['internet_allowed']}",
        f"Externe APIs erlaubt: {config['privacy']['external_api_allowed']}",
        "",
        "ENDE BERICHT",
        "=" * 70,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    smoke_dir = ROOT / "Windows_App" / "Logs" / "logging_smoke"
    logger, smoke_log_path = configure_json_logging(
        "alin.phase0.ap04",
        log_dir=smoke_dir,
        log_file="phase0_ap04_smoke.jsonl",
    )
    log_event(
        logger,
        event="phase0_ap04_logging_smoke",
        message="Synthetischer Logging-Smoke-Test",
        context={"synthetic": True, "client_data": False},
    )
    for handler in logger.handlers:
        handler.flush()

    first_line = smoke_log_path.read_text(encoding="utf-8").splitlines()[0]
    parsed_event = json.loads(first_line)

    report = render_report(config, smoke_log_path, parsed_event)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_REPORT.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
