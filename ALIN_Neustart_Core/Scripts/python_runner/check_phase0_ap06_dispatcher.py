#!/usr/bin/env python3
"""Pruefung fuer Phase 0, AP 0.6."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


REQUIRED = [
    ROOT / "alin.py",
    ROOT / "Config" / "phase0_ap06_dispatcher_v1.json",
    ROOT / "Projektplanung" / "PHASE0_AP06_DISPATCHER.md",
    ROOT / "Reports" / "PHASE0_AP06_DISPATCHER_BERICHT.txt",
    ROOT / "Windows_App" / "Logs" / "PHASE0_AP06_DISPATCHER_BERICHT.txt",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def run_dispatcher(args: list[str], env: dict[str, str] | None = None) -> tuple[int, dict]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        [sys.executable, str(ROOT / "alin.py"), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
        env=merged_env,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Dispatcher-Ausgabe ist kein JSON: {result.stdout}") from exc
    return result.returncode, payload


def main() -> int:
    for path in REQUIRED:
        if not path.exists():
            fail(f"Pflichtdatei fehlt: {path.relative_to(ROOT)}")

    code, payload = run_dispatcher(["health"])
    if code != 0 or payload["mode"] != "dry-run" or payload["status"] != "ok":
        fail("Health-Dry-run ist fehlerhaft.")

    code, payload = run_dispatcher(["--dry-run", "redline-check", "--note", "https://example.invalid"])
    if code != 2 or payload["allowed"] is not False:
        fail("Redline-Blockade liefert nicht den erwarteten Exitcode.")

    code, payload = run_dispatcher(["--execute", "safety-setting", "--admin-password", "secret"])
    if code != 3 or payload["status"] != "blocked":
        fail("Sicherheitskommando ohne Admin-Hash wurde nicht blockiert.")

    password = "synthetic-admin"
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    code, payload = run_dispatcher(
        ["--execute", "safety-setting", "--admin-password", password],
        env={"ALIN_ADMIN_PASSWORD_SHA256": digest},
    )
    if code != 0 or payload["status"] != "accepted":
        fail("Admin-Passwortpruefung mit Hash ist fehlgeschlagen.")

    report = (ROOT / "Reports" / "PHASE0_AP06_DISPATCHER_BERICHT.txt").read_text(encoding="utf-8")
    if "Standardmodus ist dry-run" not in report:
        fail("Bericht dokumentiert dry-run nicht.")

    print("PHASE 0, AP 0.6: Pruefung erfolgreich.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        raise SystemExit(1)
