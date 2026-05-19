#!/usr/bin/env python3
"""ALIN Dispatcher.

Lokale Kommandozentrale fuer sichere Wartungs- und Prueflaeufe.
Standard ist dry-run. Echte Ausfuehrung braucht --execute.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from alin_core.redline_guard import evaluate_action
from alin_core.network_guard import NetworkBlockedError, check_outbound_allowed


ADMIN_HASH_ENV = "ALIN_ADMIN_PASSWORD_SHA256"


def json_print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def password_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_admin_password(password: str | None) -> None:
    expected = os.environ.get(ADMIN_HASH_ENV)
    if not expected:
        raise PermissionError(f"{ADMIN_HASH_ENV} ist nicht gesetzt.")
    if not password:
        raise PermissionError("Admin-Passwort fehlt.")
    if password_hash(password) != expected:
        raise PermissionError("Admin-Passwort ist falsch.")


def run_python_script(script: Path, args: list[str]) -> int:
    command = [sys.executable, str(script), *args]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def command_health(mode: str) -> int:
    payload = {
        "status": "ok",
        "mode": mode,
        "service": "ALIN Dispatcher",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace": str(ROOT),
    }
    json_print(payload)
    return 0


def command_redline_check(mode: str, note: str, paths: list[str]) -> int:
    action = {"operation": "dispatcher_redline_check", "note": note, "paths": paths}
    decision = evaluate_action(action)
    payload = {
        "mode": mode,
        "status": decision.status,
        "allowed": decision.allowed,
        "findings": [finding.__dict__ for finding in decision.findings],
    }
    json_print(payload)
    return 0 if decision.allowed else 2


def command_migrate(mode: str) -> int:
    script = ROOT / "Scripts" / "python_runner" / "phase0_ap02_migration_runner.py"
    return run_python_script(script, ["--execute" if mode == "execute" else "--dry-run"])


def command_safety_setting(mode: str, password: str | None) -> int:
    if mode != "execute":
        json_print(
            {
                "mode": mode,
                "status": "dry-run",
                "message": "Sicherheitsrelevante Einstellung wuerde nur mit --execute und Admin-Passwort geaendert.",
            }
        )
        return 0
    require_admin_password(password)
    json_print(
        {
            "mode": mode,
            "status": "accepted",
            "message": "Admin-Passwort geprueft; konkrete Sicherheitsaenderungen werden in spaeteren APs implementiert.",
        }
    )
    return 0


def command_network_check(mode: str, host: str, port: int, update_click: bool) -> int:
    try:
        check_outbound_allowed(host, port, update_click=update_click)
    except NetworkBlockedError as exc:
        json_print({"mode": mode, "status": "blocked", "reason": str(exc), "host": host, "port": port})
        return 2
    json_print({"mode": mode, "status": "allowed", "host": host, "port": port})
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ALIN lokaler Dispatcher")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Nur pruefen/vorschauen.")
    mode.add_argument("--execute", action="store_true", help="Aenderungen wirklich ausfuehren.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health")

    redline = sub.add_parser("redline-check")
    redline.add_argument("--note", default="")
    redline.add_argument("--path", action="append", default=[])

    sub.add_parser("migrate")

    safety = sub.add_parser("safety-setting")
    safety.add_argument("--admin-password")

    network = sub.add_parser("network-check")
    network.add_argument("--host", required=True)
    network.add_argument("--port", type=int, default=443)
    network.add_argument("--update-click", action="store_true")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    mode = "execute" if args.execute else "dry-run"
    try:
        if args.command == "health":
            return command_health(mode)
        if args.command == "redline-check":
            return command_redline_check(mode, args.note, args.path)
        if args.command == "migrate":
            return command_migrate(mode)
        if args.command == "safety-setting":
            return command_safety_setting(mode, args.admin_password)
        if args.command == "network-check":
            return command_network_check(mode, args.host, args.port, args.update_click)
    except PermissionError as exc:
        json_print({"mode": mode, "status": "blocked", "reason": str(exc)})
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
