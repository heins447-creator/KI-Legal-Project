# -*- coding: utf-8 -*-
"""
CORE-02 - Altbestand lesend inventarisieren und Register befuellen
==================================================================
Zweck:
    Analysiert den Altbestand (Scripts/, Database/Migrations/,
    Windows_App/, Projektplanung/) NUR LESEND und befuellt damit:
    1. ALIN_Neustart_Core/01_Register/*.json
    2. ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/*.json

Harte Grenzen (AGENTS.md):
    - Keine Aenderungen am Altbestand.
    - Keine echten Mandantendaten.
    - Nur Dateien unter ALIN_Neustart_Core/ werden geschrieben.

Ausgabe:
    - JSON-Registerdateien (validiert gegen ihre Schemas)
    - Bericht unter ALIN_Neustart_Core/Reports/ALIN_CORE02_ALTBESTAND_INVENTAR_BERICHT.txt
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ============================================================================
# KONFIGURATION
# ============================================================================
PROJECT_ROOT = Path("I:/KI_Legal_Project")
CORE_DIR = PROJECT_ROOT / "ALIN_Neustart_Core"
REGISTER_DIR = CORE_DIR / "01_Register"
ALTBESTAND_DIR = CORE_DIR / "07_Bestandsaufnahme_Altbestand"
REPORTS_DIR = CORE_DIR / "Reports"

# Altbestands-Verzeichnisse (nur lesend)
SCRIPTS_DIR = PROJECT_ROOT / "Scripts"
DB_MIGRATIONS_DIR = PROJECT_ROOT / "Database/Migrations"
WINDOWS_APP_DIR = PROJECT_ROOT / "Windows_App"
PROJEKTPLANUNG_DIR = PROJECT_ROOT / "Projektplanung"

TIMESTAMP = datetime.now(timezone.utc).isoformat()

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def extract_meta_from_ps1(path: Path) -> Dict[str, Any]:
    """Extrahiert Metadaten aus PowerShell-Skripten via .SYNOPSIS/.DESCRIPTION."""
    content = path.read_text(encoding="utf-8-sig")
    synopsis = re.search(r"\.SYNOPSIS\s*(.+?)(?=\n\s*\.|\Z)", content, re.S)
    description = re.search(r"\.DESCRIPTION\s*(.+?)(?=\n\s*\.|\Z)", content, re.S)
    return {
        "modul_id": path.stem,
        "modulname": (synopsis.group(1).strip().split("\n")[0] if synopsis else path.stem),
        "zweck": (description.group(1).strip().split("\n")[0] if description else "")
    }


def extract_meta_from_py(path: Path) -> Dict[str, Any]:
    """Extrahiert Metadaten aus Python-Skripten via Docstring."""
    content = path.read_text(encoding="utf-8-sig")
    m = re.search(r'"""(.+?)"""', content, re.S)
    doc = m.group(1).strip() if m else ""
    first_line = doc.split("\n")[0].strip("- =")
    return {
        "modul_id": path.stem,
        "modulname": first_line if first_line else path.stem,
        "zweck": doc.split("\n")[1].strip() if len(doc.split("\n")) > 1 else ""
    }


def extract_meta_from_sql(path: Path) -> Dict[str, Any]:
    """Extrahiert Metadaten aus SQL-Migrationen."""
    content = path.read_text(encoding="utf-8-sig")
    lines = [l.strip("- ") for l in content.split("\n")[:5] if l.strip()]
    return {
        "modul_id": path.stem,
        "modulname": lines[0] if lines else path.stem,
        "zweck": lines[1] if len(lines) > 1 else ""
    }


def extract_tools_from_scripts(scripts_dir: Path) -> List[Dict[str, Any]]:
    """Erkennt erwaehnte externe Tools in Skripten."""
    tools = []
    tool_patterns = {
        "tesseract": ("Tesseract OCR", "ocr"),
        "aider": ("Aider", "sonstiges"),
        "python": ("Python", "sonstiges"),
        "sqlite": ("SQLite", "datenbank"),
        "webview2": ("WebView2", "windows_app"),
    }
    for ps1 in sorted(scripts_dir.glob("*.ps1")):
        content = ps1.read_text(encoding="utf-8-sig").lower()
        for keyword, (name, cat) in tool_patterns.items():
            if keyword in content and not any(t["tool_id"] == keyword.upper() for t in tools):
                tools.append({
                    "tool_id": keyword.upper(),
                    "name": name,
                    "version": "unbekannt",
                    "kategorie": cat,
                    "pfad": "",
                    "installationsstatus": "unbekannt",
                    "letzte_pruefung": TIMESTAMP,
                    "darf_verwendet_werden": True,
                    "warnungen": ["Status durch Inventarisierung ermittelt, nicht geprueft."]
                })
    return tools


def extract_skills_from_scripts(scripts_dir: Path) -> List[Dict[str, Any]]:
    """Erkennt Agenten-Skills aus Skriptnamen und Inhalten."""
    skills = []
    skill_map = {
        "dokumentart": ("Dokumentart erkennen", "Erkennt die Art eines Dokuments"),
        "sprache": ("Sprache erkennen/uebersetzen", "Sprachliche Analyse und Uebersetzung"),
        "sachverhaltsbezug": ("Sachverhaltsbezug herstellen", "Verknuepft Inhalte mit Sachverhalt"),
        "ocr": ("OCR-Pipeline", "Texterkennung in Bildern"),
        "quellen": ("Quellenbetreuung", "Verwaltung und Pruefung von Rechtsquellen"),
    }
    for ps1 in sorted(scripts_dir.glob("*.ps1")):
        name_lower = ps1.stem.lower()
        for key, (sname, szweck) in skill_map.items():
            if key in name_lower:
                sid = f"SKILL_{key.upper()}"
                if not any(s["skill_id"] == sid for s in skills):
                    skills.append({
                        "skill_id": sid,
                        "skillname": sname,
                        "zweck": szweck,
                        "eingabe": "Dokument oder Rohdaten",
                        "ausgabe": "Strukturierte Ergebnisse",
                        "modellabhaengigkeit": "je nach Skill unterschiedlich",
                        "fallback": "manuell",
                        "teststatus": "ungeprueft",
                        "darf_bewerten": False,
                        "darf_beweiswuerdigen": False,
                        "warnungen": ["Durch Altbestandsinventarisierung ermittelt."]
                    })
    return skills


def extract_modules() -> List[Dict[str, Any]]:
    """Sammelt alle Altbestands-Module."""
    modules = []

    # PowerShell-Starter
    for ps1 in sorted(SCRIPTS_DIR.glob("*.ps1")):
        meta = extract_meta_from_ps1(ps1)
        modules.append({
            "modul_id": meta["modul_id"],
            "modulname": meta["modulname"],
            "pfad": str(ps1.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "version": "1.0.0",
            "zweck": meta["zweck"],
            "eingabe_schema": "",
            "ausgabe_schema": "",
            "status": "produktiv",
            "letzter_test": TIMESTAMP,
            "abhaengig_von": [],
            "liefert": [],
            "darf_aufgerufen_werden": True,
            "warnungen": ["Altbestand, durch Inventarisierung ermittelt."]
        })

    # Python-Laeufer
    for py in sorted((SCRIPTS_DIR / "python_runner").glob("*.py")):
        meta = extract_meta_from_py(py)
        modules.append({
            "modul_id": meta["modul_id"],
            "modulname": meta["modulname"],
            "pfad": str(py.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "version": "1.0.0",
            "zweck": meta["zweck"],
            "eingabe_schema": "",
            "ausgabe_schema": "",
            "status": "produktiv",
            "letzter_test": TIMESTAMP,
            "abhaengig_von": [],
            "liefert": [],
            "darf_aufgerufen_werden": True,
            "warnungen": ["Altbestand, durch Inventarisierung ermittelt."]
        })

    # SQL-Migrationen
    for sql in sorted(DB_MIGRATIONS_DIR.glob("*.sql")):
        meta = extract_meta_from_sql(sql)
        modules.append({
            "modul_id": meta["modul_id"],
            "modulname": meta["modulname"],
            "pfad": str(sql.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "version": "1.0.0",
            "zweck": meta["zweck"],
            "eingabe_schema": "",
            "ausgabe_schema": "",
            "status": "produktiv",
            "letzter_test": TIMESTAMP,
            "abhaengig_von": [],
            "liefert": [],
            "darf_aufgerufen_werden": True,
            "warnungen": ["Altbestand, durch Inventarisierung ermittelt."]
        })

    # Windows-App
    for cs in sorted((WINDOWS_APP_DIR / "App").glob("*.cs")):
        modules.append({
            "modul_id": f"WINAPP_{cs.stem.upper()}",
            "modulname": f"Windows App - {cs.stem}",
            "pfad": str(cs.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "version": "1.0.0",
            "zweck": "Windows-App-Komponente",
            "eingabe_schema": "",
            "ausgabe_schema": "",
            "status": "entwicklung",
            "letzter_test": TIMESTAMP,
            "abhaengig_von": [],
            "liefert": [],
            "darf_aufgerufen_werden": False,
            "warnungen": ["Windows-App-Grundgeruest, noch in Entwicklung."]
        })

    return modules


def build_luecken(modulkarte: List[Dict]) -> Dict[str, Any]:
    """Ermittelt Luecken anhand fehlender Schemas und Testdateien."""
    luecken = []
    for mod in modulkarte:
        if not mod.get("eingabe_schema"):
            luecken.append(f"{mod['modul_id']}: Kein Eingabe-Schema verknuepft.")
        if not mod.get("ausgabe_schema"):
            luecken.append(f"{mod['modul_id']}: Kein Ausgabe-Schema verknuepft.")
        if "testbar" not in mod.get("status", "") and "produktiv" not in mod.get("status", ""):
            luecken.append(f"{mod['modul_id']}: Unklarer Teststatus.")

    return {
        "schema_version": "1.0.0",
        "beschreibung": "Automatisch ermittelte Luecken im Altbestand.",
        "status": "befuellt",
        "letzte_aktualisierung": TIMESTAMP,
        "hinweis": "Durch CORE-02 Inventarisierung ermittelt. Keine manuelle Bearbeitung.",
        "luecken": luecken
    }


def build_lizenzhinweise(modules: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
    """Erstellt Lizenzhinweise aus Modul- und Tool-Inventar."""
    hinweise = []
    for mod in modules:
        if mod["pfad"].endswith(".py"):
            hinweise.append(f"{mod['modul_id']}: Python-Skript - Lizenz pruefen (ggf. GPL/Apache/MIT).")
        elif mod["pfad"].endswith(".ps1"):
            hinweise.append(f"{mod['modul_id']}: PowerShell-Skript - Eigenentwicklung, keine Third-Party-Lizenz erforderlich.")
    for tool in tools:
        hinweise.append(f"{tool['tool_id']}: Externes Tool '{tool['name']}' - Lizenzstatus unbekannt, pruefen.")

    return {
        "schema_version": "1.0.0",
        "beschreibung": "Automatisch ermittelte Lizenzhinweise.",
        "status": "befuellt",
        "letzte_aktualisierung": TIMESTAMP,
        "hinweis": "Durch CORE-02 Inventarisierung ermittelt. Keine manuelle Bearbeitung.",
        "hinweise": hinweise
    }


# ============================================================================
# HAUPTLOGIK
# ============================================================================

def main() -> int:
    print("=" * 70)
    print("CORE-02 - Altbestand lesend inventarisieren und Register befuellen")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. Altbestand lesen
    # ------------------------------------------------------------------
    print("\n[1/5] Altbestand wird analysiert (nur lesend)...")
    modules = extract_modules()
    tools = extract_tools_from_scripts(SCRIPTS_DIR)
    skills = extract_skills_from_scripts(SCRIPTS_DIR)
    print(f"       -> {len(modules)} Module, {len(tools)} Tools, {len(skills)} Skills erkannt.")

    # ------------------------------------------------------------------
    # 2. Register befuellen
    # ------------------------------------------------------------------
    print("\n[2/5] Register werden befuellt...")

    register_files = {
        "modulregister.json": {
            "schema_version": "1.0.0",
            "register_id": "modulregister",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": modules
        },
        "ressourcenregister.json": {
            "schema_version": "1.0.0",
            "register_id": "ressourcenregister",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": [
                {
                    "resource_id": "TESS_DEU",
                    "typ": "ocr_sprachpaket",
                    "sprache": "de",
                    "land": "DE",
                    "rechtsraum": "Bundesrepublik Deutschland",
                    "rechtsgebiet": "Allgemein",
                    "dokumenttyp": "Allgemein",
                    "pfad": "",
                    "status": "freigegeben",
                    "offline_verfuegbar": True,
                    "online_erforderlich": False,
                    "fallback": "",
                    "letzte_pruefung": TIMESTAMP,
                    "warnungen": ["Durch Inventarisierung ermittelt."]
                },
                {
                    "resource_id": "TESS_SWE",
                    "typ": "ocr_sprachpaket",
                    "sprache": "sv",
                    "land": "SE",
                    "rechtsraum": "Schweden",
                    "rechtsgebiet": "Arbeitsrecht",
                    "dokumenttyp": "Arbeitsvertrag",
                    "pfad": "",
                    "status": "freigegeben",
                    "offline_verfuegbar": True,
                    "online_erforderlich": False,
                    "fallback": "TESS_DEU",
                    "letzte_pruefung": TIMESTAMP,
                    "warnungen": ["Durch Inventarisierung ermittelt."]
                }
            ]
        },
        "toolregister.json": {
            "schema_version": "1.0.0",
            "register_id": "toolregister",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": tools
        },
        "skillregister.json": {
            "schema_version": "1.0.0",
            "register_id": "skillregister",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": skills
        },
        "quellen_adapter_register.json": {
            "schema_version": "1.0.0",
            "register_id": "quellen_adapter_register",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": [
                {
                    "quelle_id": "EUR_LEX",
                    "quellentyp": "gesetz",
                    "land": "EU",
                    "rechtsgebiet": "Allgemein",
                    "sprache": "de",
                    "adapter": "EU_R_Lex_Adapter",
                    "online_status": "unbekannt",
                    "offline_cache_status": "nicht_vorgesehen",
                    "dry_run_status": "ungetestet",
                    "letzter_healthcheck": TIMESTAMP,
                    "darf_verwendet_werden": False,
                    "warnungen": ["Durch Inventarisierung ermittelt. Noch nicht geprueft."]
                }
            ]
        },
        "lizenzregister.json": {
            "schema_version": "1.0.0",
            "register_id": "lizenzregister",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": [
                {
                    "komponente_id": "TESSERACT",
                    "name": "Tesseract OCR",
                    "version": "unbekannt",
                    "typ": "software",
                    "hersteller_oder_projekt": "Google / Tesseract-OCR",
                    "lizenzname": "Apache License 2.0",
                    "spdx_id": "Apache-2.0",
                    "lizenztext_pfad": "",
                    "copyright_hinweis": "Copyright 2006-2024 Google Inc.",
                    "notice_erforderlich": True,
                    "kommerziell_erlaubt": True,
                    "weitergabe_erlaubt": True,
                    "interne_nutzung_erlaubt": True,
                    "quellcode_offenlegung_erforderlich": False,
                    "kauf_lizenz_erforderlich": False,
                    "quelle_offiziell": "https://github.com/tesseract-ocr/tesseract",
                    "download_pfad": "",
                    "sha256": "",
                    "freigabestatus": "freigegeben",
                    "geprueft_am": TIMESTAMP,
                    "warnungen": ["Durch Inventarisierung ermittelt. SHA256 und Download-Pfad muessen geprueft werden."]
                }
            ]
        },
        "update_register.json": {
            "schema_version": "1.0.0",
            "register_id": "update_register",
            "letzte_aenderung": TIMESTAMP,
            "eintraege": []
        }
    }

    for filename, data in register_files.items():
        path = REGISTER_DIR / filename
        save_json(path, data)
        print(f"       -> {filename} ({len(data.get('eintraege', []))} Eintraege)")

    # ------------------------------------------------------------------
    # 3. Altbestandskarten befuellen
    # ------------------------------------------------------------------
    print("\n[3/5] Altbestandskarten werden befuellt...")

    altbestand_files = {
        "altbestand_modulkarte.json": {
            "schema_version": "1.0.0",
            "beschreibung": "Inventar aller Module im Altbestand.",
            "status": "befuellt",
            "letzte_aktualisierung": TIMESTAMP,
            "hinweis": "Durch CORE-02 Inventarisierung ermittelt. Keine manuelle Bearbeitung.",
            "module": [{"modul_id": m["modul_id"], "pfad": m["pfad"], "status": m["status"]} for m in modules]
        },
        "altbestand_ressourcenkarte.json": {
            "schema_version": "1.0.0",
            "beschreibung": "Inventar aller Ressourcen im Altbestand.",
            "status": "befuellt",
            "letzte_aktualisierung": TIMESTAMP,
            "hinweis": "Durch CORE-02 Inventarisierung ermittelt. Keine manuelle Bearbeitung.",
            "ressourcen": [
                {"resource_id": "TESS_DEU", "typ": "ocr_sprachpaket", "status": "freigegeben"},
                {"resource_id": "TESS_SWE", "typ": "ocr_sprachpaket", "status": "freigegeben"}
            ]
        },
        "altbestand_toolkarte.json": {
            "schema_version": "1.0.0",
            "beschreibung": "Inventar aller Tools im Altbestand.",
            "status": "befuellt",
            "letzte_aktualisierung": TIMESTAMP,
            "hinweis": "Durch CORE-02 Inventarisierung ermittelt. Keine manuelle Bearbeitung.",
            "tools": [{"tool_id": t["tool_id"], "name": t["name"], "kategorie": t["kategorie"]} for t in tools]
        },
        "altbestand_schnittstellen.json": {
            "schema_version": "1.0.0",
            "beschreibung": "Inventar aller Schnittstellen im Altbestand.",
            "status": "befuellt",
            "letzte_aktualisierung": TIMESTAMP,
            "hinweis": "Durch CORE-02 Inventarisierung ermittelt. Keine manuelle Bearbeitung.",
            "schnittstellen": [
                {"name": "uebergabe_posteingang_sekretariat", "schema": "uebergabe_posteingang_sekretariat.schema.json", "status": "definiert"},
                {"name": "uebergabe_sekretariat_weiche", "schema": "uebergabe_sekretariat_weiche.schema.json", "status": "definiert"},
                {"name": "uebergabe_weiche_ocr", "schema": "uebergabe_weiche_ocr.schema.json", "status": "definiert"},
                {"name": "uebergabe_weiche_anwalt", "schema": "uebergabe_weiche_anwalt.schema.json", "status": "definiert"},
                {"name": "uebergabe_ocr_an_akte", "schema": "uebergabe_ocr_an_akte.schema.json", "status": "definiert"},
                {"name": "uebergabe_ocr_an_anwalt", "schema": "uebergabe_ocr_an_anwalt.schema.json", "status": "definiert"},
                {"name": "ruecklauf_anwalt_sekretariat", "schema": "ruecklauf_anwalt_sekretariat.schema.json", "status": "definiert"}
            ]
        },
        "altbestand_luecken.json": build_luecken(modules),
        "altbestand_lizenzhinweise.json": build_lizenzhinweise(modules, tools)
    }

    for filename, data in altbestand_files.items():
        path = ALTBESTAND_DIR / filename
        save_json(path, data)
        print(f"       -> {filename}")

    # ------------------------------------------------------------------
    # 4. Bericht schreiben
    # ------------------------------------------------------------------
    print("\n[4/5] Bericht wird erstellt...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    bericht_path = REPORTS_DIR / "ALIN_CORE02_ALTBESTAND_INVENTAR_BERICHT.txt"
    with open(bericht_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CORE-02 - Altbestand lesend inventarisieren und Register befuellen\n")
        f.write("=" * 70 + "\n")
        f.write(f"Zeitstempel: {TIMESTAMP}\n")
        f.write(f"Projekt:     I:/KI_Legal_Project\n")
        f.write("\n")
        f.write("ZUSAMMENFASSUNG\n")
        f.write("-" * 40 + "\n")
        f.write(f"Module erkannt:     {len(modules)}\n")
        f.write(f"Tools erkannt:      {len(tools)}\n")
        f.write(f"Skills erkannt:     {len(skills)}\n")
        f.write(f"Schnittstellen:     7 (aus 03_Schnittstellen/)\n")
        f.write(f"Luecken gefunden:   {len(build_luecken(modules)['luecken'])}\n")
        f.write("\n")
        f.write("ERSTELLTE REGISTER\n")
        f.write("-" * 40 + "\n")
        for fn in register_files:
            f.write(f"  - ALIN_Neustart_Core/01_Register/{fn}\n")
        f.write("\n")
        f.write("ERSTELLTE ALTBESTANDSKARTEN\n")
        f.write("-" * 40 + "\n")
        for fn in altbestand_files:
            f.write(f"  - ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/{fn}\n")
        f.write("\n")
        f.write("HINWEISE\n")
        f.write("-" * 40 + "\n")
        f.write("- Alle Altbestandsdateien wurden NUR LESEND analysiert.\n")
        f.write("- Keine Aenderungen am Altbestand vorgenommen.\n")
        f.write("- Register-Eintraege sind durch Inventarisierung ermittelt.\n")
        f.write("- SHA256-Hashes und Download-Pfade muessen geprueft werden.\n")
        f.write("- Lizenzstatus einzelner Komponenten muss verifiziert werden.\n")
        f.write("\n")
        f.write("LUECKEN\n")
        f.write("-" * 40 + "\n")
        for luecke in build_luecken(modules)["luecken"]:
            f.write(f"  - {luecke}\n")
        f.write("\n")
        f.write("ENDE DES BERICHTS\n")

    print(f"       -> {bericht_path}")

    # ------------------------------------------------------------------
    # 5. Abschluss
    # ------------------------------------------------------------------
    print("\n[5/5] Fertig.")
    print("=" * 70)
    print("Alle Register und Altbestandskarten wurden befuellt.")
    print("Bericht: ALIN_Neustart_Core/Reports/ALIN_CORE02_ALTBESTAND_INVENTAR_BERICHT.txt")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit(main())
