"""Tests fuer Phase 1, AP 1.3: Bootstrapper."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Config" / "phase1_ap03_bootstrapper_v1.json"
BOOTSTRAPPER = ROOT / "Scripts" / "python_runner" / "phase1_ap03_bootstrapper.py"
PYTHON = ROOT / "Tools" / "Python312" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

ALLE_TOOL_IDS = {
    "PYTHON", "POWERSHELL", "DOTNET_RUNTIME", "WEBVIEW2",
    "DUCKDB", "TESSERACT", "PADDLEOCR", "PYMUPDF",
    "PYHANKO", "MSOFFCRYPTO", "CLAMAV",
    "PILLOW", "NUMPY", "OPENCV", "OLLAMA", "ARGOS_TRANSLATE",
}


def _load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_config_exists():
    assert CONFIG.exists(), "phase1_ap03_bootstrapper_v1.json nicht gefunden"


def test_bootstrapper_script_exists():
    assert BOOTSTRAPPER.exists(), "phase1_ap03_bootstrapper.py nicht gefunden"


def test_config_phase_correct():
    config = _load_config()
    assert config["phase"] == "1"
    assert config["arbeitspaket"] == "1.3"


def test_config_hat_16_schritte():
    config = _load_config()
    assert len(config["install_schritte"]) == 16, (
        f"Erwartet 16 Schritte, gefunden: {len(config['install_schritte'])}"
    )


def test_config_alle_tool_ids_abgedeckt():
    config = _load_config()
    ids = {s["tool_id"] for s in config["install_schritte"]}
    fehlend = ALLE_TOOL_IDS - ids
    assert not fehlend, f"Fehlende Tool-IDs im Bootstrapper: {fehlend}"


def test_config_alle_schritte_haben_pruef_befehl():
    config = _load_config()
    fehlend = [s["tool_id"] for s in config["install_schritte"] if not s.get("pruef_befehl")]
    assert not fehlend, f"Tools ohne pruef_befehl: {fehlend}"


def test_bootstrapper_laeuft_durch():
    """Bootstrapper muss im --check-only Modus exit 0 liefern (alle 16 OK)."""
    result = subprocess.run(
        [str(PYTHON), str(BOOTSTRAPPER), "--check-only"],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, (
        f"Bootstrapper fehlgeschlagen:\n{result.stdout}\n{result.stderr}"
    )
    assert "16/16 Tools OK" in result.stdout


def test_alle_tools_melden_ok():
    """Jedes einzelne Tool muss OK melden."""
    result = subprocess.run(
        [str(PYTHON), str(BOOTSTRAPPER), "--check-only"],
        capture_output=True, text=True, timeout=120
    )
    ausgabe = result.stdout
    fehlende = [tid for tid in ALLE_TOOL_IDS if f"[{tid}]" in ausgabe and "FEHLT" in ausgabe.split(f"[{tid}]")[1][:50]]
    assert not fehlende, f"Tools mit FEHLT-Status: {fehlende}"
