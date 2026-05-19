#!/usr/bin/env python3
"""Phase 0, AP 0.6: Dispatcher-Bericht erzeugen."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase0_ap06_dispatcher_v1.json"
REPORT_PATH = ROOT / "Reports" / "PHASE0_AP06_DISPATCHER_BERICHT.txt"
LOG_REPORT = ROOT / "Windows_App" / "Logs" / "PHASE0_AP06_DISPATCHER_BERICHT.txt"


def run_dispatcher(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "alin.py"), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def render_report(config: dict, health_code: int, blocked_code: int, safety_code: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.6 DISPATCHER BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "Dispatcher alin.py ist angelegt.",
        "Standardmodus ist dry-run; execute muss explizit gesetzt werden.",
        "",
        "SMOKE-TESTS",
        "-" * 70,
        f"health Exitcode: {health_code}",
        f"redline block Exitcode: {blocked_code}",
        f"safety-setting ohne Admin-Hash Exitcode: {safety_code}",
        "",
        "ADMIN",
        "-" * 70,
        f"Passwort-Hash-Variable: {config['dispatcher']['admin_password_hash_env']}",
        f"Klartextspeicherung: {config['dispatcher']['stores_plaintext_password']}",
        "",
        "ENDE BERICHT",
        "=" * 70,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    health_code, _ = run_dispatcher(["--dry-run", "health"])
    blocked_code, _ = run_dispatcher(["--dry-run", "redline-check", "--note", "https://example.invalid"])
    safety_code, _ = run_dispatcher(["--execute", "safety-setting", "--admin-password", "synthetic"])
    report = render_report(config, health_code, blocked_code, safety_code)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_REPORT.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
