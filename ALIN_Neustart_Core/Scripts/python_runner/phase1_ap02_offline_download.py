"""
AP 1.2 — Werkzeuge offline herunterladen und SHA-256 pruefen.

Laedt die 6 fehlenden Tools als Offline-Pakete herunter und berechnet SHA-256.
Ergebnis: 09_Toolbibliothek/04_Hashes/SHA256_MANIFEST.csv

Aufruf: python phase1_ap02_offline_download.py [--dry-run] [--tool TOOL_ID]
"""

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "Config" / "phase1_ap02_offline_download_v1.json"
DEPOT = ROOT / "09_Toolbibliothek" / "02_Installer_Offline"
MANIFEST = ROOT / "09_Toolbibliothek" / "04_Hashes" / "SHA256_MANIFEST.csv"
PYTHON = ROOT / "Tools" / "Python312" / "python.exe"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def pip_download(paket: str, version_spec: str, zielverzeichnis: Path, dry_run: bool) -> list[Path]:
    """Laedt ein Python-Paket als Wheel herunter."""
    spezifikation = f"{paket}=={version_spec}" if ".*" not in version_spec else paket
    if ".*" in version_spec:
        spezifikation = paket

    cmd = [
        str(PYTHON), "-m", "pip", "download",
        spezifikation,
        "--dest", str(zielverzeichnis),
        "--no-deps",
        "--prefer-binary",
    ]
    print(f"  Befehl: {' '.join(cmd)}")
    if dry_run:
        print("  [DRY-RUN] Kein Download.")
        return []

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FEHLER: {result.stderr.strip()}")
        return []
    print(result.stdout.strip())
    return list(zielverzeichnis.glob("*.whl")) + list(zielverzeichnis.glob("*.tar.gz"))


def http_download(url: str, ziel: Path, dry_run: bool) -> bool:
    """Laedt eine Datei per HTTP herunter."""
    print(f"  URL: {url}")
    print(f"  Ziel: {ziel}")
    if dry_run:
        print("  [DRY-RUN] Kein Download.")
        return False

    def _fortschritt(block_num, block_size, total_size):
        if total_size > 0:
            mb_geladen = block_num * block_size / 1_048_576
            mb_gesamt = total_size / 1_048_576
            print(f"\r  {mb_geladen:.1f} / {mb_gesamt:.1f} MB", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, ziel, _fortschritt)
        print()
        return True
    except Exception as e:
        print(f"\n  FEHLER: {e}")
        return False


def lade_manifest() -> dict:
    """Laedt bestehendes Manifest (tool_id -> Zeile)."""
    eintraege = {}
    if MANIFEST.exists():
        with open(MANIFEST, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                eintraege[row["tool_id"]] = row
    return eintraege


def schreibe_manifest(eintraege: dict):
    felder = ["tool_id", "version", "datei", "sha256", "datum"]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=felder)
        writer.writeheader()
        for eintrag in sorted(eintraege.values(), key=lambda x: x["tool_id"]):
            writer.writerow(eintrag)


def verarbeite_tool(tool: dict, dry_run: bool) -> dict | None:
    tool_id = tool["tool_id"]
    unterdir = DEPOT / tool["unterverzeichnis"]
    unterdir.mkdir(parents=True, exist_ok=True)

    print(f"\n[{tool_id}] {tool.get('hinweis', '')}")

    if tool["typ"] == "python_wheel":
        dateien = pip_download(tool["paket"], tool.get("version", ""), unterdir, dry_run)
        if not dateien and not dry_run:
            return None
        if dateien:
            datei = dateien[0]
            sha = sha256_file(datei)
            return {
                "tool_id": tool_id,
                "version": tool.get("version", ""),
                "datei": str(datei.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha,
                "datum": datetime.now(timezone.utc).isoformat(),
            }
        if dry_run:
            return {
                "tool_id": tool_id,
                "version": tool.get("version", ""),
                "datei": f"09_Toolbibliothek/02_Installer_Offline/{tool['unterverzeichnis']}/{tool['paket']}.whl",
                "sha256": "dry-run",
                "datum": datetime.now(timezone.utc).isoformat(),
            }

    elif tool["typ"] == "installer":
        ziel = unterdir / tool["dateiname"]
        if ziel.exists():
            print(f"  Datei bereits vorhanden: {ziel.name} ({ziel.stat().st_size / 1_048_576:.1f} MB)")
            sha = sha256_file(ziel)
        else:
            ok = http_download(tool["download_url"], ziel, dry_run)
            if not ok and not dry_run:
                return None
            if dry_run:
                return {
                    "tool_id": tool_id,
                    "version": "1.x",
                    "datei": f"09_Toolbibliothek/02_Installer_Offline/{tool['unterverzeichnis']}/{tool['dateiname']}",
                    "sha256": "dry-run",
                    "datum": datetime.now(timezone.utc).isoformat(),
                }
            sha = sha256_file(ziel)

        return {
            "tool_id": tool_id,
            "version": "1.x",
            "datei": str(ziel.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha,
            "datum": datetime.now(timezone.utc).isoformat(),
        }

    return None


def main():
    parser = argparse.ArgumentParser(description="AP 1.2 Offline-Download")
    parser.add_argument("--dry-run", action="store_true", help="Kein tatsaechlicher Download")
    parser.add_argument("--tool", help="Nur dieses Tool verarbeiten (Tool-ID)")
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    tools = config["tools"]

    if args.tool:
        tools = [t for t in tools if t["tool_id"] == args.tool.upper()]
        if not tools:
            print(f"Tool-ID nicht gefunden: {args.tool}")
            sys.exit(1)

    manifest = lade_manifest()
    fehler = []

    for tool in tools:
        eintrag = verarbeite_tool(tool, args.dry_run)
        if eintrag:
            manifest[eintrag["tool_id"]] = eintrag
            print(f"  SHA-256: {eintrag['sha256'][:16]}...")
        else:
            fehler.append(tool["tool_id"])

    if not args.dry_run:
        schreibe_manifest(manifest)
        print(f"\nManifest geschrieben: {MANIFEST}")

    print(f"\n{'='*60}")
    print(f"Abgeschlossen: {len(manifest)} Eintraege im Manifest")
    if fehler:
        print(f"FEHLER bei: {fehler}")
        sys.exit(1)
    else:
        print("Alle Tools erfolgreich verarbeitet.")


if __name__ == "__main__":
    main()
