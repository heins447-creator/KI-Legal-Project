"""Tests fuer Phase 1, AP 1.5: MSIX-Skeleton."""

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Config" / "phase1_ap05_msix_v1.json"
MANIFEST = ROOT / "Windows_App" / "App" / "Package.appxmanifest"
CSPROJ = ROOT / "Windows_App" / "App" / "ALIN.csproj"
BUILD_SKRIPT = ROOT / "Windows_App" / "Packaging" / "build_msix.ps1"


def _load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_config_exists():
    assert CONFIG.exists()


def test_config_phase_correct():
    config = _load_config()
    assert config["phase"] == "1"
    assert config["arbeitspaket"] == "1.5"


def test_manifest_exists():
    assert MANIFEST.exists(), "Package.appxmanifest nicht gefunden"


def test_csproj_exists():
    assert CSPROJ.exists(), "ALIN.csproj nicht gefunden"


def test_build_skript_exists():
    assert BUILD_SKRIPT.exists(), "build_msix.ps1 nicht gefunden"


def test_manifest_ist_valides_xml():
    baum = ET.parse(str(MANIFEST))
    root = baum.getroot()
    assert "Package" in root.tag, f"Wurzelelement ist nicht Package: {root.tag}"


def test_manifest_hat_identity():
    baum = ET.parse(str(MANIFEST))
    ns = {"m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
    identity = baum.find("m:Identity", ns)
    assert identity is not None, "Identity-Element fehlt im Manifest"
    assert identity.get("Name") == "KanzleisoftwareALIN"
    assert identity.get("Version") is not None


def test_manifest_hat_application():
    baum = ET.parse(str(MANIFEST))
    ns = {
        "m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10",
        "uap": "http://schemas.microsoft.com/appx/manifest/uap/windows10",
    }
    apps = baum.findall(".//m:Application", ns)
    assert apps, "Kein Application-Element im Manifest"
    assert apps[0].get("Executable") == "ALIN.exe"


def test_manifest_hat_fullTrust_capability():
    inhalt = MANIFEST.read_text(encoding="utf-8")
    assert "runFullTrust" in inhalt, "runFullTrust-Capability fehlt im Manifest"


def test_build_skript_nur_pruefen():
    """build_msix.ps1 -NurPruefen muss exit 0 liefern."""
    result = subprocess.run(
        ["powershell", "-NonInteractive", "-File", str(BUILD_SKRIPT), "-NurPruefen"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, (
        f"build_msix.ps1 -NurPruefen fehlgeschlagen:\n{result.stdout}\n{result.stderr}"
    )
    assert "vorhanden" in result.stdout.lower() or "OK" in result.stdout
