"""Tests fuer Phase 1, AP 1.1: Endgueltige Werkzeugliste mit Lizenzcheck."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLREGISTER = ROOT / "01_Register" / "toolregister.json"
CONFIG = ROOT / "Config" / "phase1_ap01_toollist_v1.json"

REQUIRED_TOOL_IDS = {
    "PYTHON", "POWERSHELL", "DOTNET_RUNTIME", "WEBVIEW2",
    "DUCKDB", "TESSERACT", "PADDLEOCR", "PYMUPDF",
    "PYHANKO", "MSOFFCRYPTO", "CLAMAV",
    "PILLOW", "NUMPY", "OPENCV", "OLLAMA", "ARGOS_TRANSLATE",
}

BANNED_TOOL_IDS = {"ABBYY", "AIDER", "GIT", "SQLITE"}


def _load_register():
    return json.loads(TOOLREGISTER.read_text(encoding="utf-8"))


def _load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_toolregister_exists():
    assert TOOLREGISTER.exists(), "toolregister.json nicht gefunden"


def test_config_exists():
    assert CONFIG.exists(), "phase1_ap01_toollist_v1.json nicht gefunden"


def test_exactly_16_tools():
    data = _load_register()
    tools = data["eintraege"]
    assert len(tools) == 16, f"Erwartet 16 Tools, gefunden: {len(tools)}"


def test_required_tools_present():
    data = _load_register()
    ids = {t["tool_id"] for t in data["eintraege"]}
    missing = REQUIRED_TOOL_IDS - ids
    assert not missing, f"Fehlende Tools: {missing}"


def test_banned_tools_absent():
    data = _load_register()
    ids = {t["tool_id"] for t in data["eintraege"]}
    present = BANNED_TOOL_IDS & ids
    assert not present, f"Verbotene Tools noch vorhanden: {present}"


def test_all_tools_have_lizenz_id():
    data = _load_register()
    missing = [t["tool_id"] for t in data["eintraege"] if not t.get("lizenz_id")]
    assert not missing, f"Tools ohne lizenz_id: {missing}"


def test_all_tools_have_healthcheck_befehl():
    data = _load_register()
    missing = [t["tool_id"] for t in data["eintraege"] if not t.get("healthcheck_befehl")]
    assert not missing, f"Tools ohne healthcheck_befehl: {missing}"


def test_all_tools_darf_verwendet_werden():
    data = _load_register()
    blocked = [t["tool_id"] for t in data["eintraege"] if not t.get("darf_verwendet_werden", False)]
    assert not blocked, f"Tools nicht freigegeben: {blocked}"


def test_pymupdf_has_agpl_warning():
    data = _load_register()
    pymupdf = next(t for t in data["eintraege"] if t["tool_id"] == "PYMUPDF")
    warnings_text = " ".join(pymupdf.get("warnungen", []))
    assert "AGPL" in warnings_text or "agpl" in warnings_text.lower(), \
        "PyMuPDF muss AGPL-Warnung haben"


def test_config_phase_correct():
    config = _load_config()
    assert config["phase"] == "1"
    assert config["arbeitspaket"] == "1.1"
