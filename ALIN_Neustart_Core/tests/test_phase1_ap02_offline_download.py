"""Tests fuer Phase 1, AP 1.2: Werkzeuge offline herunterladen und SHA-256 pruefen."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Config" / "phase1_ap02_offline_download_v1.json"
MANIFEST = ROOT / "09_Toolbibliothek" / "04_Hashes" / "SHA256_MANIFEST.csv"
DEPOT = ROOT / "09_Toolbibliothek" / "02_Installer_Offline"

ERWARTETE_TOOLS = {"PADDLEOCR", "PYHANKO", "MSOFFCRYPTO", "CLAMAV", "OLLAMA", "ARGOS_TRANSLATE"}


def _load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _load_manifest():
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["tool_id"]: row for row in reader}


def test_config_exists():
    assert CONFIG.exists(), "phase1_ap02_offline_download_v1.json nicht gefunden"


def test_config_phase_correct():
    config = _load_config()
    assert config["phase"] == "1"
    assert config["arbeitspaket"] == "1.2"


def test_config_has_exactly_6_tools():
    config = _load_config()
    assert len(config["tools"]) == 6, f"Erwartet 6 Tools, gefunden: {len(config['tools'])}"


def test_config_alle_tool_ids_korrekt():
    config = _load_config()
    ids = {t["tool_id"] for t in config["tools"]}
    assert ids == ERWARTETE_TOOLS, f"Falsche Tool-IDs: {ids}"


def test_config_alle_tools_haben_unterverzeichnis():
    config = _load_config()
    fehlend = [t["tool_id"] for t in config["tools"] if not t.get("unterverzeichnis")]
    assert not fehlend, f"Tools ohne unterverzeichnis: {fehlend}"


def test_config_python_tools_haben_paket():
    config = _load_config()
    fehlend = [
        t["tool_id"] for t in config["tools"]
        if t["typ"] == "python_wheel" and not t.get("paket")
    ]
    assert not fehlend, f"Python-Tools ohne paket: {fehlend}"


def test_config_installer_tools_haben_url():
    config = _load_config()
    fehlend = [
        t["tool_id"] for t in config["tools"]
        if t["typ"] == "installer" and not t.get("download_url")
    ]
    assert not fehlend, f"Installer-Tools ohne download_url: {fehlend}"


def test_depot_verzeichnis_existiert():
    assert DEPOT.exists(), f"Depot-Verzeichnis nicht gefunden: {DEPOT}"


def test_manifest_existiert():
    """Manifest muss nach Download vorhanden sein."""
    import pytest
    if not MANIFEST.exists():
        pytest.skip(
            "SHA256_MANIFEST.csv noch nicht erstellt — "
            "Scripts/Run_PHASE1_AP02_Offline_Download.ps1 ausfuehren."
        )


def test_manifest_hat_alle_6_tools():
    if not MANIFEST.exists():
        import pytest
        pytest.skip("Manifest noch nicht erstellt — erst nach Download pruefen")
    manifest = _load_manifest()
    fehlend = ERWARTETE_TOOLS - set(manifest.keys())
    assert not fehlend, f"Fehlende Tools im Manifest: {fehlend}"


def test_manifest_alle_sha256_vorhanden():
    if not MANIFEST.exists():
        import pytest
        pytest.skip("Manifest noch nicht erstellt")
    manifest = _load_manifest()
    ungueltig = [
        tid for tid, e in manifest.items()
        if tid in ERWARTETE_TOOLS and (not e.get("sha256") or e["sha256"] == "dry-run")
    ]
    assert not ungueltig, f"Tools ohne gueltigen SHA-256: {ungueltig}"
