"""
ALIN Pre-Run-Gate Healthcheck (AP 1.4).

Prueft alle kritischen und optionalen Tools beim Start.
Blockiert den Start bei fehlenden Pflicht-Tools.

Verwendung:
    from alin_core.healthcheck import gate_check
    gate_check()  # wirft SystemExit bei kritischem Fehler
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KRITISCH = frozenset({"PYTHON", "DUCKDB", "TESSERACT", "PYMUPDF", "PILLOW", "NUMPY", "OPENCV"})
OPTIONAL = frozenset({"PADDLEOCR", "PYHANKO", "MSOFFCRYPTO", "CLAMAV", "ARGOS_TRANSLATE", "OLLAMA"})
INFRASTRUKTUR = frozenset({"POWERSHELL", "DOTNET_RUNTIME", "WEBVIEW2"})

TIMEOUT = 5


@dataclass
class ToolStatus:
    tool_id: str
    ok: bool
    detail: str
    kategorie: str  # kritisch | optional | infrastruktur


@dataclass
class HealthResult:
    zeitstempel: str
    gesamt_ok: bool
    kritisch_fehler: list[str] = field(default_factory=list)
    optionale_warnungen: list[str] = field(default_factory=list)
    details: list[ToolStatus] = field(default_factory=list)


def _import_check(modul: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(modul)
        version = getattr(mod, "__version__", None) or "ok"
        return True, str(version).split("\n")[0][:40]
    except ImportError as e:
        return False, str(e)[:60]


def _cmd_check(befehl: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(befehl, shell=True, capture_output=True, text=True, timeout=TIMEOUT)
        ausgabe = (r.stdout + r.stderr).strip().split("\n")[0][:60]
        return r.returncode == 0, ausgabe
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:60]


def _pruefe_tool(tool_id: str) -> tuple[bool, str]:
    if tool_id == "PYTHON":
        return True, f"Python {sys.version.split()[0]}"
    if tool_id == "DUCKDB":
        return _import_check("duckdb")
    if tool_id == "PYMUPDF":
        return _import_check("fitz")
    if tool_id == "PILLOW":
        ok, detail = _import_check("PIL")
        if not ok:
            return _import_check("PIL.Image")
        return ok, detail
    if tool_id == "NUMPY":
        return _import_check("numpy")
    if tool_id == "OPENCV":
        return _import_check("cv2")
    if tool_id == "PADDLEOCR":
        return _import_check("paddleocr")
    if tool_id == "PYHANKO":
        return _import_check("pyhanko.sign")
    if tool_id == "MSOFFCRYPTO":
        return _import_check("msoffcrypto")
    if tool_id == "ARGOS_TRANSLATE":
        return _import_check("argostranslate")
    if tool_id == "TESSERACT":
        tess = ROOT / "Tools" / "Tesseract-OCR" / "tesseract.exe"
        if tess.exists():
            return _cmd_check(f'"{tess}" --version')
        return _cmd_check("tesseract --version")
    if tool_id == "CLAMAV":
        for pfad in [
            ROOT / "Tools" / "ClamAV" / "clamav-1.5.2.win.x64" / "clamscan.exe",
            ROOT / "Tools" / "ClamAV" / "clamav-1.3.1.win.x64" / "clamscan.exe",
            Path("C:/Program Files/ClamAV/clamscan.exe"),
        ]:
            if pfad.exists():
                return _cmd_check(f'"{pfad}" --version')
        return _cmd_check("clamscan --version")
    if tool_id == "OLLAMA":
        return _cmd_check("ollama --version")
    if tool_id == "POWERSHELL":
        return _cmd_check('powershell -Command "$PSVersionTable.PSVersion.Major"')
    if tool_id == "DOTNET_RUNTIME":
        return _cmd_check("dotnet --version")
    if tool_id == "WEBVIEW2":
        return _cmd_check(
            'reg query "HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients'
            '\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv'
        )
    return False, f"unbekannte Tool-ID: {tool_id}"


def run_healthcheck(stille: bool = False) -> HealthResult:
    ergebnis = HealthResult(
        zeitstempel=datetime.now(timezone.utc).isoformat(),
        gesamt_ok=True,
    )

    alle_tools = [
        *[(t, "kritisch") for t in sorted(KRITISCH)],
        *[(t, "optional") for t in sorted(OPTIONAL)],
        *[(t, "infrastruktur") for t in sorted(INFRASTRUKTUR)],
    ]

    for tool_id, kategorie in alle_tools:
        ok, detail = _pruefe_tool(tool_id)
        status = ToolStatus(tool_id=tool_id, ok=ok, detail=detail, kategorie=kategorie)
        ergebnis.details.append(status)

        if not ok:
            if kategorie == "kritisch":
                ergebnis.kritisch_fehler.append(tool_id)
                ergebnis.gesamt_ok = False
            else:
                ergebnis.optionale_warnungen.append(tool_id)

        if not stille:
            symbol = "OK" if ok else ("FEHLT" if kategorie == "kritisch" else "WARNUNG")
            print(f"  [{symbol:7}] {tool_id}: {detail}")

    return ergebnis


def gate_check(stille: bool = False) -> HealthResult:
    """Fuehrt den Healthcheck durch und wirft SystemExit bei kritischen Fehlern."""
    if not stille:
        print("ALIN Healthcheck...")

    ergebnis = run_healthcheck(stille=stille)

    log_pfad = ROOT / "Windows_App" / "Logs" / "healthcheck_report.json"
    log_pfad.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "zeitstempel": ergebnis.zeitstempel,
        "gesamt_ok": ergebnis.gesamt_ok,
        "kritisch_fehler": ergebnis.kritisch_fehler,
        "optionale_warnungen": ergebnis.optionale_warnungen,
        "details": [
            {"tool_id": d.tool_id, "ok": d.ok, "detail": d.detail, "kategorie": d.kategorie}
            for d in ergebnis.details
        ],
    }
    log_pfad.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if ergebnis.kritisch_fehler:
        print(f"\nKRITISCH: Fehlende Pflicht-Tools: {ergebnis.kritisch_fehler}")
        print("ALIN kann nicht gestartet werden. Bitte Bootstrapper ausfuehren:")
        print("  Scripts/Run_PHASE1_AP03_Bootstrapper.ps1")
        sys.exit(1)

    if ergebnis.optionale_warnungen and not stille:
        print(f"  Hinweis: Optionale Tools nicht verfuegbar: {ergebnis.optionale_warnungen}")

    return ergebnis


if __name__ == "__main__":
    gate_check()
