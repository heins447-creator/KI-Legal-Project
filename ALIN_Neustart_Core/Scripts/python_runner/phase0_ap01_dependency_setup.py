#!/usr/bin/env python3
"""Phase 0, AP 0.1: Dependency-Setup protokollieren.

Der Laeufer erzeugt den Abnahmebericht fuer pyproject, Lockfile und
Offline-Wheelhouse-Policy. Er fuehrt keine Installation und keinen
Netzzugriff aus.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase0_ap01_dependency_policy_v1.json"
REPORT_PATH = ROOT / "Reports" / "PHASE0_AP01_DEPENDENCY_SETUP_BERICHT.txt"
LOG_PATH = ROOT / "Windows_App" / "Logs" / "PHASE0_AP01_DEPENDENCY_SETUP_BERICHT.txt"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def command_available(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except OSError as exc:
        return False, str(exc)
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def read_lock_packages(lock_path: Path) -> list[str]:
    packages: list[str] = []
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        packages.append(stripped)
    return packages


def render_report(policy: dict, uv_ok: bool, uv_output: str, packages: list[str]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.1 DEPENDENCY-SETUP BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        f"Arbeitswurzel: {ROOT}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "pyproject.toml, requirements.lock und Offline-Wheelhouse-Policy sind angelegt.",
        "Es wurde keine Installation und kein Internetzugriff ausgefuehrt.",
        "",
        "UV-STATUS",
        "-" * 70,
        f"uv verfuegbar: {'ja' if uv_ok else 'nein'}",
        f"uv Ausgabe: {uv_output or 'keine'}",
        "",
        "LOCKFILE",
        "-" * 70,
        f"Lockfile: {policy['files']['lockfile']}",
        f"Gepinnte Pakete: {len(packages)}",
        "",
        "WHEELHOUSE",
        "-" * 70,
        f"Pfad: {policy['files']['wheelhouse']}",
        "Status: Struktur angelegt, Spiegelbefuellung steht noch aus.",
        "",
        "NAECHSTER KONTROLLIERTER SCHRITT",
        "-" * 70,
        policy["next_controlled_step"],
        "",
        "HINWEIS",
        "-" * 70,
        "Ein echtes uv.lock wurde noch nicht generiert, weil uv nicht installiert ist und keine Installation ohne Zustimmung erfolgt.",
        "Der aktuelle Lock ist ein offline nutzbares requirements.lock fuer uv pip sync.",
        "",
        "ENDE BERICHT",
        "=" * 70,
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    policy = load_json(CONFIG_PATH)
    lock_path = ROOT / policy["files"]["lockfile"]
    packages = read_lock_packages(lock_path)
    uv_ok, uv_output = command_available(["uv", "--version"])

    report = render_report(policy, uv_ok, uv_output, packages)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_PATH.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
