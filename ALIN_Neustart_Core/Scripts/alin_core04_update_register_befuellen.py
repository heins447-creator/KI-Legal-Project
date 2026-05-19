# -*- coding: utf-8 -*-
"""
CORE-04 – Update-Register initial befüllen

Befüllt beide Update-Register-Dateien (01_Register/ und 10_Update_Ueberwachung/)
mit initialen Update-Einträgen für alle bekannten Komponenten.

Quellen:
- Toolregister (bekannte Tools)
- Lizenzregister (bekannte Lizenzen)
- Ressourcenregister (bekannte Ressourcen)
- Projektplanung/Dokumentation (weitere Komponenten)
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("I:/KI_Legal_Project")
CORE = ROOT / "ALIN_Neustart_Core"
REGISTER_DIR = CORE / "01_Register"
UPDATE_DIR = CORE / "10_Update_Ueberwachung/00_Update_Register"
REPORTS_DIR = CORE / "Reports"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_update_entry(
    update_id: str,
    komponente_id: str,
    aktuelle_version: str = "unbekannt",
    verfuegbare_version: str = "unbekannt",
    quelle: str = "",
    lizenz: str = "",
    pruefstatus: str = "ungeprueft",
    auto_pruefung: bool = False,
    auto_ersetzung: bool = False,
    rollback: bool = False,
    warnungen: list = None
) -> dict:
    if warnungen is None:
        warnungen = []
    return {
        "update_id": update_id,
        "komponente_id": komponente_id,
        "aktuelle_version": aktuelle_version,
        "verfuegbare_version": verfuegbare_version,
        "quelle": quelle,
        "lizenz": lizenz,
        "hash": "",
        "pruefstatus": pruefstatus,
        "automatische_pruefung": auto_pruefung,
        "automatische_ersetzung": auto_ersetzung,
        "rollback_moeglich": rollback,
        "freigabeprotokoll": [],
        "warnungen": warnungen
    }


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    print("=" * 70)
    print("CORE-04 – Update-Register initial befüllen")
    print("=" * 70)

    # Bekannte Komponenten aus vorherigen Registern und Projektstruktur
    eintraege = []

    # 1. Tesseract OCR (aus Toolregister + Lizenzregister)
    eintraege.append(build_update_entry(
        update_id="UPD_TESSERACT",
        komponente_id="TESSERACT",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://github.com/tesseract-ocr/tesseract/releases",
        lizenz="Apache-2.0",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Version muss manuell geprüft werden", "Offline-Installation erforderlich"]
    ))

    # 2. Python Interpreter
    eintraege.append(build_update_entry(
        update_id="UPD_PYTHON",
        komponente_id="PYTHON",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://www.python.org/downloads/",
        lizenz="PSF-2.0",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Version über py --version prüfbar", "Kompatibilität mit allen Modulen testen"]
    ))

    # 3. Aider (AI Coding Agent)
    eintraege.append(build_update_entry(
        update_id="UPD_AIDER",
        komponente_id="AIDER",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://github.com/paul-gauthier/aider/releases",
        lizenz="Apache-2.0",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Nur im Entwicklungsmodus verwendet", "Keine Mandantendaten verarbeiten"]
    ))

    # 4. Git
    eintraege.append(build_update_entry(
        update_id="UPD_GIT",
        komponente_id="GIT",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://git-scm.com/downloads",
        lizenz="GPL-2.0",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Systemkomponente", "Keine API-Keys in Git speichern"]
    ))

    # 5. .NET Runtime (für Windows-App)
    eintraege.append(build_update_entry(
        update_id="UPD_DOTNET",
        komponente_id="DOTNET_RUNTIME",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://dotnet.microsoft.com/download",
        lizenz="MIT",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Voraussetzung für Windows-App", "Offline-Installer bereithalten"]
    ))

    # 6. WebView2 Runtime (für Windows-App UI)
    eintraege.append(build_update_entry(
        update_id="UPD_WEBVIEW2",
        komponente_id="WEBVIEW2_RUNTIME",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://developer.microsoft.com/microsoft-edge/webview2/",
        lizenz="Microsoft-Software-Lizenz",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Voraussetzung für WebView2-UI", "Evergreen-Installer bevorzugen"]
    ))

    # 7. PowerShell (Windows-Systemkomponente)
    eintraege.append(build_update_entry(
        update_id="UPD_POWERSHELL",
        komponente_id="POWERSHELL",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://github.com/PowerShell/PowerShell/releases",
        lizenz="MIT",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Windows-Systemkomponente", "Kompatibilität mit Start-Skripten prüfen"]
    ))

    # 8. SQLite (Datenbank-Engine)
    eintraege.append(build_update_entry(
        update_id="UPD_SQLITE",
        komponente_id="SQLITE",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://sqlite.org/download.html",
        lizenz="Public-Domain",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["Datenbank-Engine", "Migrationstests bei Update erforderlich"]
    ))

    # 9. Tesseract Deutsch Sprachpaket
    eintraege.append(build_update_entry(
        update_id="UPD_TESS_DEU",
        komponente_id="TESS_DEU",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://github.com/tesseract-ocr/tessdata",
        lizenz="Apache-2.0",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["OCR-Sprachpaket", "Offline-Verfügbarkeit prüfen"]
    ))

    # 10. Tesseract Schwedisch Sprachpaket
    eintraege.append(build_update_entry(
        update_id="UPD_TESS_SWE",
        komponente_id="TESS_SWE",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="https://github.com/tesseract-ocr/tessdata",
        lizenz="Apache-2.0",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=False,
        warnungen=["OCR-Sprachpaket", "Offline-Verfügbarkeit prüfen"]
    ))

    # 11. Windows-App (eigene Anwendung)
    eintraege.append(build_update_entry(
        update_id="UPD_WINDOWS_APP",
        komponente_id="WINDOWS_APP",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="Internes Build-System",
        lizenz="Proprietär",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=True,
        warnungen=["Eigenentwicklung", "Rollback-Plan bei Deployment beachten"]
    ))

    # 12. ALIN Core-Module (Gesamtsystem)
    eintraege.append(build_update_entry(
        update_id="UPD_ALIN_CORE",
        komponente_id="ALIN_CORE",
        aktuelle_version="unbekannt",
        verfuegbare_version="unbekannt",
        quelle="Git-Repository",
        lizenz="Proprietär",
        pruefstatus="ungeprueft",
        auto_pruefung=False,
        auto_ersetzung=False,
        rollback=True,
        warnungen=["Gesamtsystem-Update", "Alle Register neu validieren"]
    ))

    # Register-Daten erstellen
    register_data = {
        "schema_version": "1.0.0",
        "register_id": "update_register",
        "letzte_aenderung": now_iso(),
        "eintraege": eintraege
    }

    # Beide Pfade schreiben (01_Register/ und 10_Update_Ueberwachung/)
    path_01 = REGISTER_DIR / "update_register.json"
    path_10 = UPDATE_DIR / "ALIN_UPDATE_REGISTER.json"

    save_json(path_01, register_data)
    save_json(path_10, register_data)

    print(f"Update-Register befüllt: {len(eintraege)} Einträge")
    print(f"Geschrieben nach: {path_01}")
    print(f"Geschrieben nach: {path_10}")

    # Bericht erstellen
    bericht = []
    bericht.append("=" * 70)
    bericht.append("CORE-04 UPDATE-REGISTER BEFÜLLUNG")
    bericht.append("=" * 70)
    bericht.append(f"Zeitstempel: {now_iso()}")
    bericht.append(f"Anzahl Einträge: {len(eintraege)}")
    bericht.append("")
    bericht.append("Einträge:")
    for e in eintraege:
        bericht.append(f"  {e['update_id']} -> {e['komponente_id']} (Status: {e['pruefstatus']})")
    bericht.append("")
    bericht.append("Hinweise:")
    bericht.append("- Alle Versionen sind 'unbekannt' – manuelle Prüfung erforderlich")
    bericht.append("- Alle Prüfstatus sind 'ungeprueft' – Healthcheck noch nicht durchgeführt")
    bericht.append("- Automatische Prüfung/Ersetzung ist deaktiviert (Dry-Run-Standard)")
    bericht.append("- Rollback ist nur für Windows-App und ALIN-Core möglich")
    bericht.append("=" * 70)

    bericht_text = "\n".join(bericht)
    bericht_path = REPORTS_DIR / "ALIN_CORE04_UPDATE_REGISTER_BERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write(bericht_text)
    print(f"\nBericht geschrieben nach: {bericht_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
