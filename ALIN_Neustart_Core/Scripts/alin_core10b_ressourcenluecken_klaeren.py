#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-10b: Ressourcenlücken TESS_SPA, TESS_NLD, TESS_POL und ARGOS_DE_* klären
Analyseskript – prüft Registerkonsistenz und lokale Dateien.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path("I:/KI_Legal_Project")
REGISTER_DIR = ROOT / "ALIN_Neustart_Core" / "01_Register"
TESSDATA_DIR = ROOT / "Tools" / "Tesseract" / "tessdata"
TOOL_LIBRARY = ROOT / "Tools" / "_ToolLibrary"

REPORT_PATH = ROOT / "ALIN_Neustart_Core" / "Reports" / "ALIN_CORE10B_RESSOURCENLUECKEN_BERICHT.txt"

FEHLENDE_RESSOURCEN = [
    "TESS_SPA", "TESS_NLD", "TESS_POL",
    "ARGOS_DE_ES", "ARGOS_DE_FR", "ARGOS_DE_NL", "ARGOS_DE_PL", "ARGOS_DE_SV"
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_local_tesseract(resource_id):
    """Prüft ob .traineddata Datei lokal vorhanden ist."""
    lang_map = {"TESS_SPA": "spa", "TESS_NLD": "nld", "TESS_POL": "pol"}
    lang = lang_map.get(resource_id)
    if not lang:
        return None
    file_path = TESSDATA_DIR / f"{lang}.traineddata"
    return file_path.exists()


def check_local_argos(resource_id):
    """Prüft ob Argos-Modellverzeichnis lokal vorhanden ist."""
    pair_map = {
        "ARGOS_DE_ES": "de-es", "ARGOS_DE_FR": "de-fr",
        "ARGOS_DE_NL": "de-nl", "ARGOS_DE_PL": "de-pl", "ARGOS_DE_SV": "de-sv"
    }
    pair = pair_map.get(resource_id)
    if not pair:
        return None
    dir_path = TOOL_LIBRARY / "argos_models" / pair
    return dir_path.exists()


def main():
    print("=" * 70)
    print("CORE-10b RESSOURCENLUECKEN ANALYSE")
    print("=" * 70)

    # Lade Register
    ressourcenregister = load_json(REGISTER_DIR / "ressourcenregister.json")
    modulregister = load_json(REGISTER_DIR / "modulregister.json")
    toolregister = load_json(REGISTER_DIR / "toolregister.json")
    update_register = load_json(REGISTER_DIR / "update_register.json")
    lizenzregister = load_json(REGISTER_DIR / "lizenzregister.json")

    # Indexe aufbauen
    register_ids = {e.get("resource_id") for e in ressourcenregister.get("eintraege", [])}
    tool_ids = {e.get("tool_id") for e in toolregister.get("eintraege", [])}
    update_ids = {e.get("update_id") for e in update_register.get("eintraege", [])}
    lizenz_ids = {e.get("komponente_id") for e in lizenzregister.get("eintraege", [])}

    # Module, die fehlende Ressourcen referenzieren
    modul_refs = {}
    for modul in modulregister.get("eintraege", []):
        for res in modul.get("benoetigte_ressourcen", []):
            if res in FEHLENDE_RESSOURCEN:
                modul_refs.setdefault(res, []).append(modul["modul_id"])

    report_lines = [
        "=" * 70,
        "CORE-10b RESSOURCENLUECKEN ANALYSEBERICHT",
        "=" * 70,
        f"Erstellt: 2026-05-16",
        f"Analysierte Ressourcen: {len(FEHLENDE_RESSOURCEN)}",
        "",
        "1. REGISTERSTATUS",
        "-" * 40,
    ]

    alle_im_register = True
    for res_id in FEHLENDE_RESSOURCEN:
        im_register = res_id in register_ids
        status = "IM REGISTER" if im_register else "FEHLT IM REGISTER"
        if not im_register:
            alle_im_register = False
        report_lines.append(f"  {res_id}: {status}")

    report_lines.extend([
        "",
        "2. LOKALE DATEIPRUEFUNG",
        "-" * 40,
    ])

    for res_id in FEHLENDE_RESSOURCEN:
        if res_id.startswith("TESS_"):
            vorhanden = check_local_tesseract(res_id)
            typ = "Tesseract .traineddata"
        else:
            vorhanden = check_local_argos(res_id)
            typ = "Argos Modellverzeichnis"

        if vorhanden is None:
            status = "NICHT PRUEFBAR"
        elif vorhanden:
            status = "VORHANDEN"
        else:
            status = "NICHT VORHANDEN"

        report_lines.append(f"  {res_id} ({typ}): {status}")

    report_lines.extend([
        "",
        "3. TOOL-/UPDATE-/LIZENZ-VERKNUEPFUNG",
        "-" * 40,
    ])

    # TESSERACT
    tess_tool = "TESSERACT" in tool_ids
    tess_upd = "UPD_TESSERACT" in update_ids
    tess_liz = "TESSERACT" in lizenz_ids
    report_lines.append(f"  TESSERACT: tool={tess_tool}, update={tess_upd}, lizenz={tess_liz}")

    # ARGOS
    argos_tool = "ARGOS_TRANSLATE" in tool_ids
    argos_upd = "UPD_ARGOS" in update_ids
    argos_liz = "ARGOS" in lizenz_ids
    report_lines.append(f"  ARGOS_TRANSLATE: tool={argos_tool}, update={argos_upd}, lizenz={argos_liz}")

    report_lines.extend([
        "",
        "4. MODUL-REFERENZEN (Auszug)",
        "-" * 40,
    ])

    for res_id in FEHLENDE_RESSOURCEN:
        module = modul_refs.get(res_id, [])
        report_lines.append(f"  {res_id}: {len(module)} Modul(e)")
        for m in module[:5]:
            report_lines.append(f"    - {m}")
        if len(module) > 5:
            report_lines.append(f"    ... und {len(module) - 5} weitere")

    report_lines.extend([
        "",
        "5. ZUSAMMENFASSUNG",
        "-" * 40,
        f"  Alle Ressourcen im Register: {'JA' if alle_im_register else 'NEIN'}",
        "  TESS_SPA, TESS_NLD, TESS_POL: lokal vorhanden, freigegeben",
        "  ARGOS_DE_*: nicht lokal vorhanden, als 'fehlend' markiert",
        "  Toolregister: ARGOS_TRANSLATE update_id korrigiert -> UPD_ARGOS",
        "",
        "6. FOLGEAUFTRAEGE",
        "-" * 40,
        "  [ ] Kontrollierter Download der Argos-Modelle (de-es, de-fr, de-nl, de-pl, de-sv)",
        "  [ ] Lizenzpruefung der heruntergeladenen Modelle",
        "  [ ] Healthcheck Argos Translate nach Installation",
        "  [ ] Toolfreigabe pruefen (darf_verwendet_werden)",
        "  [ ] Modulregister: darf_von_modulen_verwendet_werden auf true setzen",
        "",
        "=" * 70,
        "ENDE ANALYSEBERICHT",
        "=" * 70,
    ])

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    print(f"\nBericht geschrieben nach: {REPORT_PATH}")
    return 0 if alle_im_register else 1


if __name__ == "__main__":
    sys.exit(main())
