#!/usr/bin/env python3
"""
Check-File fuer WINAPP – Windows App Build und Release (Vorbereitung)
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
EINGABEN = {
    "csproj": BASE_DIR / "Windows_App" / "App" / "KI_Legal_WindowsApp.csproj",
    "release_checklist": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "RELEASE_CHECKLIST.md",
    "changelog": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "CHANGELOG.md",
    "rollback_plan": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "ROLLBACK_PLAN.md",
    "version_json": BASE_DIR / "ALIN_Neustart_Core" / "16_Build_Release" / "VERSION.json",
    "build_script": BASE_DIR / "Windows_App" / "Scripts" / "Build_App.ps1",
}


def pruefe() -> tuple[bool, list[str]]:
    fehler = []

    for name, pfad in EINGABEN.items():
        if not pfad.exists():
            fehler.append(f"Eingabe fehlt: {name} -> {pfad}")

    csproj = EINGABEN["csproj"]
    if csproj.exists():
        inhalt = csproj.read_text(encoding="utf-8")
        if "<Project" not in inhalt:
            fehler.append("csproj enthaelt kein <Project-Tag")
        if "<TargetFramework" not in inhalt and "<TargetFrameworks" not in inhalt:
            fehler.append("csproj enthaelt kein TargetFramework")

    version = EINGABEN["version_json"]
    if version.exists():
        try:
            daten = json.loads(version.read_text(encoding="utf-8"))
            if "status" not in daten:
                fehler.append("VERSION.json enthaelt kein 'status'-Feld")
        except json.JSONDecodeError as e:
            fehler.append(f"VERSION.json ist kein gueltiges JSON: {e}")

    bericht_dir = BASE_DIR / "ALIN_Neustart_Core" / "Reports"
    if not bericht_dir.exists():
        fehler.append(f"Bericht-Verzeichnis fehlt: {bericht_dir}")

    return (len(fehler) == 0, fehler)


def main() -> int:
    ok, fehler = pruefe()
    if ok:
        print("[OK] Alle Pruefungen bestanden.")
        return 0
    else:
        print("[FEHLER] Pruefungen fehlgeschlagen:")
        for f in fehler:
            print(f"  - {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
