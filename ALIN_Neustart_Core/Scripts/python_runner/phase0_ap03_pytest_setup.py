#!/usr/bin/env python3
"""Phase 0, AP 0.3: pytest-Setup protokollieren.

Der Laeufer prueft die Teststruktur und schreibt den Bericht. Er installiert
pytest nicht und oeffnet keine Internetverbindung.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase0_ap03_pytest_setup_v1.json"
REPORT_PATH = ROOT / "Reports" / "PHASE0_AP03_PYTEST_SETUP_BERICHT.txt"
LOG_PATH = ROOT / "Windows_App" / "Logs" / "PHASE0_AP03_PYTEST_SETUP_BERICHT.txt"


def pytest_available() -> tuple[bool, str]:
    spec = importlib.util.find_spec("pytest")
    if spec is None:
        return False, "pytest nicht installiert"
    import pytest  # type: ignore

    return True, getattr(pytest, "__version__", "Version unbekannt")


def collect_test_files() -> list[Path]:
    tests_dir = ROOT / "tests"
    return sorted(tests_dir.glob("test_*.py"))


def render_report(config: dict, available: bool, pytest_status: str, test_files: list[Path]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "PHASE 0, AP 0.3 PYTEST-SETUP BERICHT",
        "=" * 70,
        f"Erstellt: {timestamp}",
        f"Arbeitswurzel: {ROOT}",
        "",
        "ERGEBNIS",
        "-" * 70,
        "pytest-Konfiguration und tests-Verzeichnis sind angelegt.",
        "Es wurde keine Installation und kein Internetzugriff ausgefuehrt.",
        "",
        "PYTEST-STATUS",
        "-" * 70,
        f"pytest verfuegbar: {'ja' if available else 'nein'}",
        f"Status: {pytest_status}",
        "",
        "TESTDATEIEN",
        "-" * 70,
    ]
    for path in test_files:
        lines.append(f"- {path.relative_to(ROOT)}")
    if not test_files:
        lines.append("- keine")
    lines.extend(
        [
            "",
            "POLICY",
            "-" * 70,
            *config["test_policy"],
            "",
            "HINWEIS",
            "-" * 70,
            "Die pytest-Ausfuehrung ist vorbereitet. In der aktuellen Projektlaufzeit fehlt pytest noch; Installation erfolgt spaeter nur kontrolliert aus dem Offline-Wheelhouse.",
            "",
            "ENDE BERICHT",
            "=" * 70,
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    available, pytest_status = pytest_available()
    test_files = collect_test_files()
    report = render_report(config, available, pytest_status, test_files)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    LOG_PATH.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
