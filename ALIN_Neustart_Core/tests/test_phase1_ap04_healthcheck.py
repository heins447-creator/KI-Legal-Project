"""Tests fuer Phase 1, AP 1.4: Healthcheck Pre-Run-Gate."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Config" / "phase1_ap04_healthcheck_v1.json"
HEALTHCHECK = ROOT / "alin_core" / "healthcheck.py"
ALIN = ROOT / "alin.py"
PYTHON = ROOT / "Tools" / "Python312" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


def _load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_config_exists():
    assert CONFIG.exists()


def test_healthcheck_modul_exists():
    assert HEALTHCHECK.exists(), "alin_core/healthcheck.py nicht gefunden"


def test_config_phase_correct():
    config = _load_config()
    assert config["phase"] == "1"
    assert config["arbeitspaket"] == "1.4"


def test_config_kritische_tools_enthalten():
    config = _load_config()
    kritisch = set(config["kritische_tools"])
    pflicht = {"PYTHON", "DUCKDB", "PYMUPDF", "TESSERACT"}
    assert pflicht <= kritisch, f"Pflichttools nicht als kritisch markiert: {pflicht - kritisch}"


def _python_mit_pfad(code: str, timeout: int = 30) -> subprocess.CompletedProcess:
    skript = f"import sys; sys.path.insert(0, r'{ROOT}'); {code}"
    return subprocess.run(
        [str(PYTHON), "-c", skript],
        capture_output=True, text=True, cwd=str(ROOT), timeout=timeout
    )


def test_healthcheck_module_importierbar():
    result = _python_mit_pfad(
        "from alin_core.healthcheck import gate_check, run_healthcheck; print('ok')"
    )
    assert result.returncode == 0, f"Import fehlgeschlagen: {result.stderr[:300]}"
    assert "ok" in result.stdout


def test_healthcheck_laeuft_durch():
    """run_healthcheck() muss alle kritischen Tools als OK melden."""
    result = _python_mit_pfad(
        "from alin_core.healthcheck import run_healthcheck; "
        "r = run_healthcheck(stille=True); "
        "assert not r.kritisch_fehler, f'Kritisch: {r.kritisch_fehler}'; "
        "print('OK')"
    )
    assert result.returncode == 0, f"Healthcheck fehlgeschlagen:\n{result.stdout}\n{result.stderr}"
    assert "OK" in result.stdout


def test_healthcheck_report_wird_geschrieben():
    result = _python_mit_pfad(
        "from alin_core.healthcheck import run_healthcheck; "
        "run_healthcheck(stille=True); print('done')"
    )
    assert result.returncode == 0, result.stderr[:200]
    report_pfad = ROOT / "Windows_App" / "Logs" / "healthcheck_report.json"
    assert report_pfad.exists(), "Healthcheck-Report wurde nicht geschrieben"
    report = json.loads(report_pfad.read_text(encoding="utf-8"))
    assert "zeitstempel" in report
    assert "gesamt_ok" in report
    assert "details" in report


def test_alin_health_befehl():
    """alin.py health muss exit 0 liefern und JSON mit status-Feld ausgeben."""
    result = subprocess.run(
        [str(PYTHON), str(ALIN), "health"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=30
    )
    assert result.returncode == 0, f"alin.py health fehlgeschlagen:\n{result.stdout}\n{result.stderr}"
    # JSON-Block aus Ausgabe extrahieren (kann nach Healthcheck-Textausgabe kommen)
    zeilen = result.stdout.strip().splitlines()
    json_text = "\n".join(l for l in zeilen if l.strip().startswith("{") or l.strip().startswith("}") or
                          (zeilen.index(l) > 0 and zeilen[zeilen.index(l)-1].strip().startswith("{")))
    # Suche nach erstem { bis letzte }
    start = result.stdout.find("{")
    ende = result.stdout.rfind("}") + 1
    assert start >= 0, "Kein JSON in Ausgabe"
    daten = json.loads(result.stdout[start:ende])
    assert daten.get("status") in ("ok", "degraded")
