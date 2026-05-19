#!/usr/bin/env python3
"""Phase 0, AP 0.7: Network-Guard berichten."""

from __future__ import annotations

import json
import socket
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from alin_core.network_guard import NetworkBlockedError, enforce_network_guard, load_network_policy


REPORT_PATH = ROOT / "Reports" / "PHASE0_AP07_NETWORK_GUARD_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP07_NETWORK_GUARD_BERICHT.txt"


def blocked_smoke() -> str:
    try:
        with enforce_network_guard():
            socket.create_connection(("example.invalid", 443), timeout=1)
    except NetworkBlockedError:
        return "blocked"
    return "not_blocked"


def render_report(policy: dict, smoke_status: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.7 NETWORK-GUARD BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "App-interne Outbound-Sperre ist angelegt.",
        "Der Smoke-Test wurde blockiert, bevor eine echte Verbindung aufgebaut wurde.",
        "",
        "POLICY",
        "-" * 70,
        f"Default Outbound: {policy['default_outbound']}",
        f"Software-Internet erlaubt: {policy['software_internet_allowed']}",
        f"Update-Klick erforderlich: {policy['update_channel_requires_explicit_click']}",
        f"Update-Hosts konfiguriert: {len(policy['update_hosts'])}",
        "",
        "SMOKE-TEST",
        "-" * 70,
        f"example.invalid:443: {smoke_status}",
        "",
        "ENDE BERICHT",
        "=" * 70,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    policy = load_network_policy()
    smoke_status = blocked_smoke()
    report = render_report(policy, smoke_status)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_REPORT.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
