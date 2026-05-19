#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.7."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from alin_core.network_guard import NetworkBlockedError, check_outbound_allowed, enforce_network_guard, load_network_policy


REQUIRED = [
    ROOT / "Config" / "phase0_ap07_network_guard_v1.json",
    ROOT / "alin_core" / "network_guard.py",
    ROOT / "Projektplanung" / "PHASE0_AP07_NETWORK_GUARD.md",
    ROOT / "Reports" / "PHASE0_AP07_NETWORK_GUARD_BERICHT.txt",
    ROOT / "Windows_App" / "Logs" / "PHASE0_AP07_NETWORK_GUARD_BERICHT.txt",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    for path in REQUIRED:
        if not path.exists():
            fail(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")

    policy = load_network_policy()
    if policy["default_outbound"] != "deny":
        fail("Default-Outbound muss deny sein.")
    if policy["software_internet_allowed"] is not False:
        fail("Software-Internet muss standardmaessig verboten sein.")

    try:
        check_outbound_allowed("example.invalid", 443)
    except NetworkBlockedError:
        pass
    else:
        fail("Direkte Outbound-Pruefung blockiert nicht.")

    with enforce_network_guard():
        try:
            socket.create_connection(("example.invalid", 443), timeout=1)
        except NetworkBlockedError:
            pass
        else:
            fail("socket.create_connection wurde nicht blockiert.")

    update_policy = {
        "default_outbound": "deny",
        "update_channel_requires_explicit_click": True,
        "update_hosts": ["updates.alin.invalid"],
    }
    check_outbound_allowed("updates.alin.invalid", 443, update_click=True, policy=update_policy)

    result = subprocess.run(
        [sys.executable, str(ROOT / "alin.py"), "--dry-run", "network-check", "--host", "example.invalid"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    payload = json.loads(result.stdout)
    if result.returncode != 2 or payload["status"] != "blocked":
        fail("Dispatcher network-check blockiert nicht korrekt.")

    report = (ROOT / "Reports" / "PHASE0_AP07_NETWORK_GUARD_BERICHT.txt").read_text(encoding="utf-8")
    if "example.invalid:443: blocked" not in report:
        fail("Bericht dokumentiert blockierten Smoke-Test nicht.")

    print("PHASE 0, AP 0.7: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
