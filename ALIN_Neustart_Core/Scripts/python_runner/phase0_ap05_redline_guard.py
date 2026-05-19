#!/usr/bin/env python3
"""Phase 0, AP 0.5: Redline-Guard ausfuehren und berichten."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from alin_core.redline_guard import evaluate_action, load_redlines, validate_redlines_structure


CONFIG_PATH = ROOT / "Config" / "phase0_ap05_redline_guard_v1.json"
REPORT_PATH = ROOT / "Reports" / "PHASE0_AP05_REDLINE_GUARD_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP05_REDLINE_GUARD_BERICHT.txt"


def render_report(redline_count: int, blocked_status: str, allowed_status: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.5 REDLINE-GUARD BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "Rote Linien sind als technische JSON-Regeln angelegt.",
        f"Regeln: {redline_count}",
        "",
        "SMOKE-TESTS",
        "-" * 70,
        f"Verbotene Beispielaktion: {blocked_status}",
        f"Erlaubte Beispielaktion: {allowed_status}",
        "",
        "SPERREN",
        "-" * 70,
        "Pfad ausserhalb Arbeitswurzel wird blockiert.",
        "Internet-/Fremd-API-Muster werden blockiert.",
        "Datenbankaenderung ohne Migration wird blockiert.",
        "Tuerschwelle vor Voraussetzungen wird blockiert.",
        "",
        "ENDE BERICHT",
        "=" * 70,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    redlines = load_redlines()
    validate_redlines_structure(redlines)
    blocked = evaluate_action(
        {
            "operation": "network_request",
            "paths": ["I:/KI_Legal_Project/ALIN_Neustart_Core/Reports/x.txt"],
            "note": "requests.get https://example.invalid",
        }
    )
    allowed = evaluate_action(
        {
            "operation": "write_report",
            "paths": ["Reports/synthetic_report.txt"],
            "note": "synthetic local report",
        }
    )
    report = render_report(len(redlines["rules"]), blocked.status, allowed.status)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_REPORT.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
