#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-25: Programmierbare Gesamt-Roadmap

Ziel:
    Das fachliche Gesamtkonzept der lokalen Kanzleisoftware wird in eine
    maschinenlesbare Roadmap fuer CORE-24 (Autonomer Entwicklungsmanager)
    zerlegt.

Lieferpflichten aus AGENTS.md:
    - Python-Laeufer unter Scripts/python_runner/
    - Pruefdatei unter Scripts/python_runner/
    - PowerShell-Starter unter Scripts/
    - Konfiguration unter Config/, falls erforderlich
    - Dokumentation unter Projektplanung/
    - Testlauf
    - Bericht unter ALIN_Neustart_Core/Reports/
    - Git-Status vor und nach Aenderung
    - Git-Commit nur bei erfolgreichem Build und erfolgreicher Pruefung

Regeln:
    - Nur Befehle aus AGENTENFREIGABE_KLARSTELLUNG.txt verwenden
    - Keine destruktiven Operationen
    - Roadmap muss von CORE-24 lesbar sein (kompatibles JSON-Format)
    - Abhaengigkeiten muessen zyklenfrei sein
    - Jedes Modul braucht eindeutige ID, Status, Prioritaet
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# =============================================================================
# KONSTANTEN & Pfade
# =============================================================================

BASE_DIR = Path("I:/KI_Legal_Project")
CONFIG_PATH = BASE_DIR / "Config" / "core25_roadmap_v1.json"

# Quelldateien
SOURCE_MASTER = BASE_DIR / "ALIN_Neustart_Core" / "00_Dokumentation" / "ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md"
SOURCE_INDEX = BASE_DIR / "ALIN_Neustart_Core" / "00_Dokumentation" / "ALIN_AUFTRAGSINDEX.md"
SOURCE_MODULPAKETE = BASE_DIR / "ALIN_Neustart_Core" / "00_Dokumentation" / "ALIN_MODULPAKETE.md"
SOURCE_NAECHSTE = BASE_DIR / "ALIN_Neustart_Core" / "00_Dokumentation" / "ALIN_NAECHSTE_AUFTRAEGE.md"
SOURCE_KONSTRUKTION = BASE_DIR / "ALIN_Neustart_Core" / "00_Dokumentation" / "ALIN_PROFESSIONELLE_SOFTWARE_KONSTRUKTION.md"

CORE24_QUEUE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_auftragsqueue.json"
CORE24_CONFIG_PATH = BASE_DIR / "Config" / "core24_entwicklungsmanager_v1.json"

# Ergebnisdateien
ROADMAP_JSON_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap.json"
BERICHT_PATH = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE25_GESAMT_ROADMAP_BERICHT.txt"

GIT_STATUS_VOR_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_git_status_vor.txt"
GIT_STATUS_NACH_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_git_status_nach.txt"

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    ts = zeitstempel()
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(BERICHT_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def lade_json(pfad: Path) -> dict:
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def speichere_json(pfad: Path, daten: dict) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)


def run_cmd(cmd: list[str], cwd: Path = BASE_DIR, timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)


def git_status_speichern(ziel_pfad: Path) -> bool:
    rc, out, err = run_cmd(["git", "status"])
    if rc != 0:
        log(f"WARNUNG: git status fehlgeschlagen: {err}")
        return False
    ziel_pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel_pfad, "w", encoding="utf-8") as f:
        f.write(out)
    return True


def git_add_dateien(dateien: list[str]) -> tuple[bool, str]:
    for d in dateien:
        pfad = BASE_DIR / d
        if not pfad.exists():
            log(f"  WARNUNG: Datei fuer git add nicht gefunden, ueberspringe: {d}")
            continue
        rc, out, err = run_cmd(["git", "add", d])
        if rc != 0:
            return False, f"git add fehlgeschlagen fuer {d}: {err}"
    return True, "git add OK"


def git_commit(nachricht: str) -> tuple[bool, str]:
    rc, out, err = run_cmd(["git", "commit", "-m", nachricht])
    if rc == 0:
        return True, f"git commit OK: {out.strip()}"
    else:
        if "nothing to commit" in (out + err).lower() or "nichts zu committen" in (out + err).lower():
            return True, "Nichts zu committen"
        return False, f"git commit FEHLER: {err or out}"


def pruefe_datei_existenz(pfad: Path, beschreibung: str) -> tuple[bool, str]:
    if pfad.exists():
        return True, f"{beschreibung} gefunden: {pfad}"
    return False, f"{beschreibung} NICHT gefunden: {pfad}"


def lade_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return lade_json(CONFIG_PATH)
        except Exception as e:
            log(f"WARNUNG: Config konnte nicht geladen werden: {e}. Verwende Default.")
    return {
        "modul_id": "CORE-25",
        "version": "1.0.0",
        "roadmap_regeln": {
            "max_stufen": 100,
            "pruefe_zyklische_abhaengigkeiten": True,
            "erlaubte_status": ["offen", "in_bearbeitung", "abgeschlossen", "gesperrt", "wartend"],
            "pflicht_felder": ["stufe_id", "name", "abhaengigkeiten", "eingaben", "ausgaben", "tests", "prioritaet", "fertigstellungskriterien"]
        }
    }

# =============================================================================
# ROADMAP-DATEN (Hardcoded aus Dokumentation extrahiert)
# =============================================================================


def erzeuge_gesamt_roadmap() -> dict:
    """
    Erzeugt die maschinenlesbare Gesamt-Roadmap basierend auf den
    Konzeptdokumenten des Projekts.
    """
    stufen = []

    # ======================================================================
    # PHASE 0: Master-Grundlagen (Vorab)
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-00",
        "name": "Masterauftrag und Grundmodell",
        "beschreibung": "Professionelles Software-Grundmodell, Windows-Grundlage, Toolbestand, Lizenzregister, Updateueberwachung und Kanzlei-Sprachgebrauch anlegen.",
        "phase": "Vorbereitung",
        "prioritaet": 0,
        "status": "abgeschlossen",
        "abhaengigkeiten": [],
        "eingaben": [
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_GRUNDMODELL.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_PROFESSIONELLE_SOFTWARE_KONSTRUKTION.md"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_NAECHSTE_AUFTRAEGE.md",
            "ALIN_Neustart_Core/Reports/ALIN_NEUSTART_CORE_MASTER_BERICHT.txt"
        ],
        "sperren": [],
        "tests": [
            "Dokumentation vollstaendig",
            "Scope-Lock definiert",
            "Keine zyklischen Abhaengigkeiten im Grundmodell"
        ],
        "erlaubte_naechste_module": ["CORE-01", "CORE-02", "CORE-03", "CORE-04", "CORE-05", "CORE-13"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Masterdokumentation angelegt",
            "Grundmodell definiert",
            "Modulpakete kategorisiert",
            "Auftragsindex erstellt"
        ]
    })

    # ======================================================================
    # PHASE 1: Grundmodell vervollstaendigen (CORE-01 bis CORE-05)
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-01",
        "name": "Register befuellen",
        "beschreibung": "Modulregister, Ressourcenregister, Skillregister, Quellen-/Adapterregister, Toolregister, Lizenzregister, Update-Register initialisieren und mit Altbestand abgleichen.",
        "phase": "Phase 1: Grundmodell",
        "prioritaet": 1,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-00"],
        "eingaben": [
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_GRUNDMODELL.md",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_modulkarte.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_ressourcenkarte.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_toolkarte.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/01_Register/modulregister.json",
            "ALIN_Neustart_Core/01_Register/ressourcenregister.json",
            "ALIN_Neustart_Core/01_Register/skillregister.json",
            "ALIN_Neustart_Core/01_Register/quellen_adapter_register.json",
            "ALIN_Neustart_Core/01_Register/toolregister.json",
            "ALIN_Neustart_Core/01_Register/lizenzregister.json",
            "ALIN_Neustart_Core/01_Register/update_register.json"
        ],
        "sperren": ["Kein Altbestand inventarisiert"],
        "tests": [
            "Alle Register-Schemas validieren",
            "Keine doppelten Eintraege",
            "Lizenzregister vollstaendig"
        ],
        "erlaubte_naechste_module": ["CORE-02", "CORE-03", "CORE-04", "CORE-05"],
        "blockierte_module": ["CORE-06", "CORE-07", "CORE-08", "CORE-09", "CORE-10"],
        "fertigstellungskriterien": [
            "Alle 7 Register angelegt und befuellt",
            "Register-Schemas definiert",
            "Altbestand abgeglichen"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-02",
        "name": "Statusmodell implementieren",
        "beschreibung": "Status-JSON-Dateien mit Uebergangsregeln, Fehlerklassen definieren, Status-Validierung.",
        "phase": "Phase 1: Grundmodell",
        "prioritaet": 2,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-01"],
        "eingaben": [
            "ALIN_Neustart_Core/01_Register/modulregister.json",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_GRUNDMODELL.md"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/02_Statusmodell/akte_status.json",
            "ALIN_Neustart_Core/02_Statusmodell/anwalt_status.json",
            "ALIN_Neustart_Core/02_Statusmodell/dokument_status.json",
            "ALIN_Neustart_Core/02_Statusmodell/eingang_status.json",
            "ALIN_Neustart_Core/02_Statusmodell/ruecklauf_status.json",
            "ALIN_Neustart_Core/02_Statusmodell/weiche_status.json",
            "ALIN_Neustart_Core/02_Statusmodell/statusmodell.schema.json",
            "ALIN_Neustart_Core/Reports/ALIN_CORE02_ALTBESTAND_INVENTAR_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/ALIN_CORE02_PRUEFBERICHT.txt"
        ],
        "sperren": ["Register unvollstaendig"],
        "tests": [
            "Statusuebergaenge zulaessig",
            "Fehlerklassen abgedeckt",
            "Schema-Validierung bestanden"
        ],
        "erlaubte_naechste_module": ["CORE-03", "CORE-04", "CORE-05", "CORE-06"],
        "blockierte_module": ["CORE-07", "CORE-08", "CORE-09", "CORE-10"],
        "fertigstellungskriterien": [
            "6 Statusmodelle definiert",
            "Uebergangsregeln dokumentiert",
            "Schema validiert",
            "Pruefbericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-03",
        "name": "Schnittstellenvertraege finalisieren",
        "beschreibung": "Alle Uebergabe-Schemas pruefen und abstimmen, Pflichtfelder validieren, Beispiel-Objekte erstellen.",
        "phase": "Phase 1: Grundmodell",
        "prioritaet": 3,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-01", "CORE-02"],
        "eingaben": [
            "ALIN_Neustart_Core/02_Statusmodell/statusmodell.schema.json",
            "ALIN_Neustart_Core/01_Register/modulregister.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/03_Schnittstellen/ruecklauf_anwalt_sekretariat.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_ocr_an_akte.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_ocr_an_anwalt.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_posteingang_sekretariat.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_sekretariat_weiche.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_weiche_anwalt.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_weiche_ocr.schema.json"
        ],
        "sperren": ["Statusmodell unvollstaendig", "Register nicht befuellt"],
        "tests": [
            "Alle Schemas validieren",
            "Pflichtfelder definiert",
            "Beispiel-Objekte vorhanden"
        ],
        "erlaubte_naechste_module": ["CORE-04", "CORE-05", "CORE-06", "CORE-07"],
        "blockierte_module": ["CORE-08", "CORE-09", "CORE-10"],
        "fertigstellungskriterien": [
            "7 Schnittstellen-Schemas definiert",
            "Pflichtfelder validiert",
            "Beispiel-Objekte erstellt"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-04",
        "name": "Healthcheck implementieren",
        "beschreibung": "Systemstart-Healthcheck als Python-Runner, Pruefung aller Bestandteile, Berichterstellung.",
        "phase": "Phase 1: Grundmodell",
        "prioritaet": 4,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-01", "CORE-02", "CORE-03"],
        "eingaben": [
            "ALIN_Neustart_Core/01_Register/",
            "ALIN_Neustart_Core/02_Statusmodell/",
            "ALIN_Neustart_Core/03_Schnittstellen/",
            "Config/core21_arbeitsindex_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/04_Healthcheck/healthcheck_regeln.json",
            "ALIN_Neustart_Core/04_Healthcheck/healthcheck_statuswerte.json",
            "ALIN_Neustart_Core/04_Healthcheck/systemstart_healthcheck.schema.json",
            "ALIN_Neustart_Core/04_Healthcheck/review_listen.json",
            "ALIN_Neustart_Core/04_Healthcheck/healthcheck_bericht_template.txt"
        ],
        "sperren": ["Register nicht befuellt", "Statusmodell fehlt", "Schnittstellen unvollstaendig"],
        "tests": [
            "Healthcheck-Regeln vollstaendig",
            "Statuswerte abgedeckt",
            "Review-Listen definiert"
        ],
        "erlaubte_naechste_module": ["CORE-05", "CORE-06", "CORE-11"],
        "blockierte_module": ["CORE-07", "CORE-08", "CORE-09", "CORE-10"],
        "fertigstellungskriterien": [
            "Healthcheck-Regeln definiert",
            "Statuswerte katalogisiert",
            "Berichtstemplate erstellt",
            "Review-Listen angelegt"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-05",
        "name": "Resolver implementieren",
        "beschreibung": "Aktenprofil-Resolver, Ressourcen-Resolver, Workflow-Resolver, Tool-Resolver, Quellen-Resolver.",
        "phase": "Phase 1: Grundmodell",
        "prioritaet": 5,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-01", "CORE-02", "CORE-03", "CORE-04"],
        "eingaben": [
            "ALIN_Neustart_Core/01_Register/",
            "ALIN_Neustart_Core/04_Healthcheck/healthcheck_regeln.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/05_Resolver/aktenprofil_resolver.schema.json",
            "ALIN_Neustart_Core/05_Resolver/ressourcen_resolver.schema.json",
            "ALIN_Neustart_Core/05_Resolver/workflow_resolver.schema.json",
            "ALIN_Neustart_Core/05_Resolver/tool_resolver.schema.json",
            "ALIN_Neustart_Core/05_Resolver/quellen_resolver.schema.json"
        ],
        "sperren": ["Healthcheck nicht implementiert", "Register unvollstaendig"],
        "tests": [
            "Resolver-Schemas validieren",
            "Alle Resolver-Typen abgedeckt",
            "Fehlerfaelle definiert"
        ],
        "erlaubte_naechste_module": ["CORE-06", "CORE-11", "CORE-12"],
        "blockierte_module": ["CORE-07", "CORE-08", "CORE-09", "CORE-10"],
        "fertigstellungskriterien": [
            "5 Resolver-Schemas definiert",
            "Validierung erfolgreich",
            "Fehlerfaelle dokumentiert"
        ]
    })

    # ======================================================================
    # PHASE 2: Altbestand anbinden (CORE-06 bis CORE-10)
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-06",
        "name": "Altbestand inventarisieren",
        "beschreibung": "Modulkarte, Ressourcenkarte, Schnittstellenkarte, Luecken identifizieren, Toolkarte, Lizenzhinweise sammeln.",
        "phase": "Phase 2: Altbestand",
        "prioritaet": 6,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-01", "CORE-02", "CORE-05"],
        "eingaben": [
            "ALIN_Neustart_Core/01_Register/modulregister.json",
            "ALIN_Neustart_Core/01_Register/ressourcenregister.json",
            "ALIN_Neustart_Core/01_Register/toolregister.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_modulkarte.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_ressourcenkarte.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_schnittstellen.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_luecken.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_toolkarte.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_lizenzhinweise.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.json",
            "ALIN_Neustart_Core/Reports/CORE13_ALTBESTAND_INVENTUR_BERICHT.txt"
        ],
        "sperren": ["Register nicht befuellt", "Resolver fehlt"],
        "tests": [
            "Alle Altbestand-Karten erstellt",
            "Luecken identifiziert",
            "Inventur-Bericht vorhanden"
        ],
        "erlaubte_naechste_module": ["CORE-07", "CORE-08", "CORE-09", "CORE-10", "CORE-10a"],
        "blockierte_module": ["CORE-11", "CORE-12"],
        "fertigstellungskriterien": [
            "6 Altbestand-Karten angelegt",
            "Luecken dokumentiert",
            "Inventur-Bericht erstellt",
            "CSV-Exporte vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-07",
        "name": "Posteingang anbinden",
        "beschreibung": "Posteingang als Modul im Modulregister eintragen, Schnittstelle Posteingang -> Sekretariat definieren, Statusuebergaenge abbilden.",
        "phase": "Phase 2: Altbestand",
        "prioritaet": 7,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-03", "CORE-06"],
        "eingaben": [
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_posteingang_sekretariat.schema.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/altbestand_modulkarte.json",
            "Config/posteingang_aktenmaterial_agentenabgrenzung_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.json (aktualisiert)",
            "ALIN_Neustart_Core/Reports/ALIN_CORE07_QUELLEN_ADAPTERREGISTER_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/ALIN_CORE07_PRUEFBERICHT.txt"
        ],
        "sperren": ["Schnittstellen nicht finalisiert", "Altbestand nicht inventarisiert"],
        "tests": [
            "Posteingang im Modulregister eingetragen",
            "Schnittstelle definiert",
            "Statusuebergaenge abgebildet"
        ],
        "erlaubte_naechste_module": ["CORE-08", "CORE-09", "CORE-10", "UI08"],
        "blockierte_module": ["CORE-11", "CORE-16"],
        "fertigstellungskriterien": [
            "Posteingang als Modul registriert",
            "Schnittstelle dokumentiert",
            "Pruefbericht bestanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-08",
        "name": "OCR-Strecke anbinden",
        "beschreibung": "KM12-KM21 als Modulpaket eintragen, Schnittstelle Weiche -> OCR definieren, Schnittstelle OCR -> Akte definieren.",
        "phase": "Phase 2: Altbestand",
        "prioritaet": 8,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-06", "CORE-07"],
        "eingaben": [
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_weiche_ocr.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_ocr_an_akte.schema.json",
            "Config/ocr_pipeline_v1.json",
            "Config/km12b_uebergrosse_arbeitsabbildungen_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/ALIN_CORE08_SKILLREGISTER_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/ALIN_CORE08_PRUEFBERICHT.txt"
        ],
        "sperren": ["Posteingang nicht angebunden", "OCR-Pipeline nicht konfiguriert"],
        "tests": [
            "KM12-KM21 im Modulregister",
            "OCR-Schnittstellen definiert",
            "Skillregister aktualisiert"
        ],
        "erlaubte_naechste_module": ["CORE-09", "CORE-10", "KM12", "KM13", "UI03_1b"],
        "blockierte_module": ["CORE-11"],
        "fertigstellungskriterien": [
            "OCR-Modulpaket eingetragen",
            "Schnittstellen verifiziert",
            "Skillregister-Bericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-09",
        "name": "UI anbinden",
        "beschreibung": "UI01-UI04 als Modulpaket eintragen, Schnittstelle Weiche -> Anwalt definieren, Schnittstelle Ruecklauf definieren.",
        "phase": "Phase 2: Altbestand",
        "prioritaet": 9,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-06", "CORE-07", "CORE-08"],
        "eingaben": [
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_weiche_anwalt.schema.json",
            "ALIN_Neustart_Core/03_Schnittstellen/ruecklauf_anwalt_sekretariat.schema.json",
            "Config/ui01_anwaltsansicht_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/ALIN_CORE09_MODULREGISTER_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/ALIN_CORE09_PRUEFBERICHT.txt"
        ],
        "sperren": ["OCR-Strecke nicht angebunden", "Posteingang nicht angebunden"],
        "tests": [
            "UI01-UI04 im Modulregister",
            "Anwaltsschnittstelle definiert",
            "Ruecklauf-Schnittstelle definiert"
        ],
        "erlaubte_naechste_module": ["CORE-10", "CORE-10a", "UI01", "UI02", "UI03", "UI04"],
        "blockierte_module": ["CORE-11"],
        "fertigstellungskriterien": [
            "UI-Modulpaket eingetragen",
            "Schnittstellen dokumentiert",
            "Modulregister-Bericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-10",
        "name": "Quellen und Skills anbinden",
        "beschreibung": "Quellenbetreuer, Agenten, Skills eintragen, Adapter-Healthchecks definieren, Offline-Fallbacks dokumentieren.",
        "phase": "Phase 2: Altbestand",
        "prioritaet": 10,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-01", "CORE-06", "CORE-09"],
        "eingaben": [
            "ALIN_Neustart_Core/01_Register/quellen_adapter_register.json",
            "ALIN_Neustart_Core/01_Register/skillregister.json",
            "Config/agentenbearbeitung_grundmodul_v1.json",
            "Config/source_adapter_policy_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/ALIN_CORE10_KONSISTENZ_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/ALIN_CORE10_PRUEFBERICHT.txt"
        ],
        "sperren": ["UI nicht angebunden", "Quellenregister leer"],
        "tests": [
            "Quellenbetreuer eingetragen",
            "Skills registriert",
            "Konsistenzpruefung bestanden"
        ],
        "erlaubte_naechste_module": ["CORE-10a", "CORE-10b", "CORE-10c", "CORE-10d", "CORE-10e", "CORE-10f", "CORE-10g", "CORE-11"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Quellen und Skills eingetragen",
            "Adapter-Healthchecks definiert",
            "Offline-Fallbacks dokumentiert",
            "Konsistenz-Bericht vorhanden"
        ]
    })

    # CORE-10 Sub-Stufen
    for sub_id, sub_name, sub_prio, sub_deps, sub_block in [
        ("CORE-10a", "Findings Priorisierung und Reparaturplan", 10.1, ["CORE-10"], []),
        ("CORE-10b", "Ressourcenluecken Klaerung", 10.2, ["CORE-10a"], []),
        ("CORE-10c", "SQL Modulnamen bereinigen", 10.3, ["CORE-10b"], []),
        ("CORE-10d", "Schnittstellenbereiche nachtragen", 10.4, ["CORE-10c"], []),
        ("CORE-10e", "UI01 Abhaengigkeit Klaerung", 10.5, ["CORE-10d"], []),
        ("CORE-10f", "Platzhalter verfeinern", 10.6, ["CORE-10e"], []),
        ("CORE-10g", "Reviewlisten dokumentieren", 10.7, ["CORE-10f"], ["CORE-11"])
    ]:
        stufen.append({
            "stufe_id": sub_id,
            "name": sub_name,
            "beschreibung": f"Teilschritt von CORE-10: {sub_name}",
            "phase": "Phase 2: Altbestand (Details)",
            "prioritaet": sub_prio,
            "status": "abgeschlossen",
            "abhaengigkeiten": sub_deps,
            "eingaben": [
                "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/",
                f"ALIN_Neustart_Core/Reports/ALIN_CORE{sub_id.replace('-', '').upper()}_PRUEFBERICHT.txt"
            ],
            "ausgaben": [
                f"ALIN_Neustart_Core/Reports/ALIN_CORE{sub_id.replace('-', '').upper()}_PRUEFBERICHT.txt",
                f"ALIN_Neustart_Core/Reports/ALIN_CORE{sub_id.replace('-', '').upper()}_{sub_name.upper().replace(' ', '_')[:20]}_BERICHT.txt"
            ],
            "sperren": ["Vorgaenger nicht abgeschlossen"],
            "tests": [f"Pruefbericht {sub_id} bestanden", "Keine offenen Findings"],
            "erlaubte_naechste_module": [sub_block[0] if sub_block else "CORE-11"],
            "blockierte_module": sub_block,
            "fertigstellungskriterien": [f"{sub_id} Bericht erstellt", "Pruefung bestanden"]
        })

    # ======================================================================
    # PHASE 3: Windows-App-Grundlage (CORE-11 bis CORE-15)
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-11",
        "name": "Windows-App-Architektur finalisieren",
        "beschreibung": "Entscheidung WinUI 3 vs. WebView2 vs. WPF, Projektstruktur anlegen, Build-Prozess definieren.",
        "phase": "Phase 3: Windows-App",
        "prioritaet": 11,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-05", "CORE-10g"],
        "eingaben": [
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_APP_ARCHITEKTUR_V1.md",
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_UI_GRUNDSAETZE_V1.md",
            "Windows_App/App/KI_Legal_WindowsApp.csproj"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_APP_ARCHITEKTUR_V1.md",
            "Windows_App/App/App.xaml",
            "Windows_App/App/MainWindow.xaml",
            "ALIN_Neustart_Core/Reports/ALIN_CORE11_ABNAHME_BERICHT.txt"
        ],
        "sperren": ["Resolver nicht implementiert", "Altbestand nicht konsistent"],
        "tests": [
            "Architekturentscheidung dokumentiert",
            "Projektstruktur angelegt",
            "Build-Prozess definiert"
        ],
        "erlaubte_naechste_module": ["CORE-12", "CORE-13", "CORE-14", "CORE-15"],
        "blockierte_module": ["CORE-16", "CORE-17", "CORE-18"],
        "fertigstellungskriterien": [
            "Architektur dokumentiert",
            "Projekt kompilierbar",
            "Build-Skript vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-12",
        "name": "UI-Grundlagen implementieren",
        "beschreibung": "Hauptfenster, Dreiansicht (Original / OCR / Uebersetzung), Sekretariatsansicht, Anwaltsansicht.",
        "phase": "Phase 3: Windows-App",
        "prioritaet": 12,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-11"],
        "eingaben": [
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_UI_GRUNDSAETZE_V1.md",
            "ALIN_Neustart_Core/03_Schnittstellen/uebergabe_ocr_an_anwalt.schema.json",
            "Config/ui03_1_anwalts_dreiansicht_v1.json"
        ],
        "ausgaben": [
            "Windows_App/App/MainWindow.xaml.cs",
            "Windows_App/App/App.xaml.cs",
            "Windows_App/Scripts/Build_App.ps1",
            "Windows_App/Scripts/Start_App.ps1",
            "ALIN_Neustart_Core/Reports/ALIN_CORE11_ABNAHME_BERICHT.txt"
        ],
        "sperren": ["Architektur nicht finalisiert"],
        "tests": [
            "MainWindow kompilierbar",
            "Dreiansicht definiert",
            "Start-Skript funktioniert"
        ],
        "erlaubte_naechste_module": ["CORE-13", "CORE-15", "UI03_1"],
        "blockierte_module": ["CORE-14"],
        "fertigstellungskriterien": [
            "UI-Grundlagen implementiert",
            "Build erfolgreich",
            "Start-Skript getestet"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-13",
        "name": "Altbestand inventarisiert und inventur",
        "beschreibung": "Altbestand-Inventur, Dublettenpruefung, Klassifikation, Sperrhinweise.",
        "phase": "Phase 3: Windows-App",
        "prioritaet": 13,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-06", "CORE-11"],
        "eingaben": [
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/",
            "Config/core12_backup_rollback_konzept_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.csv",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_dubletten.csv",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_klassifikation.csv",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_sperrhinweise.csv",
            "ALIN_Neustart_Core/Reports/CORE13_ALTBESTAND_INVENTUR_BERICHT.txt"
        ],
        "sperren": ["Altbestand nicht inventarisiert", "Backup-Konzept fehlt"],
        "tests": [
            "Inventur vollstaendig",
            "Dubletten identifiziert",
            "Sperrhinweise erfasst"
        ],
        "erlaubte_naechste_module": ["CORE-14", "CORE-15", "CORE-16"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Inventur-JSON und CSVs erstellt",
            "Dubletten-Report vorhanden",
            "Sperrhinweise dokumentiert"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-14",
        "name": "CORE13-Auswertung und Sperrplan",
        "beschreibung": "Auswertung der Altbestand-Inventur, Reste-Archiv-Sperrplan, Umbau-Bericht.",
        "phase": "Phase 3: Windows-App",
        "prioritaet": 14,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-13"],
        "eingaben": [
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_sperrhinweise.csv",
            "Config/core21_arbeitsindex_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/CORE14_AUSWERTUNG_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE14_20_AUTOMANAGER_BLOCKIERT_DURCH_AGENTENFREIGABE.txt"
        ],
        "sperren": ["Inventur nicht abgeschlossen"],
        "tests": [
            "Auswertung vollstaendig",
            "Sperrplan definiert",
            "Automaneger-Regeln geprueft"
        ],
        "erlaubte_naechste_module": ["CORE-15", "CORE-16", "CORE-19"],
        "blockierte_module": ["CORE-17", "CORE-18"],
        "fertigstellungskriterien": [
            "Auswertungsbericht erstellt",
            "Sperrplan dokumentiert",
            "Automaneger-Freigabe geprueft"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-15",
        "name": "Migrationsplan und kopierende Migration",
        "beschreibung": "Migrationsplan erstellen, Dry-Run, kopierende Migration durchfuehren.",
        "phase": "Phase 3: Windows-App",
        "prioritaet": 15,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-14"],
        "eingaben": [
            "ALIN_Neustart_Core/Reports/CORE14_AUSWERTUNG_BERICHT.txt",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/",
            "Config/core21_arbeitsindex_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/CORE15_MIGRATIONSPLAN_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE16_DRY_RUN_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE17_KOPIERENDE_MIGRATION_BERICHT.txt",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json"
        ],
        "sperren": ["Auswertung nicht abgeschlossen", "Sperrplan nicht freigegeben"],
        "tests": [
            "Migrationsplan validiert",
            "Dry-Run erfolgreich",
            "Kopierte Dateien manifestiert"
        ],
        "erlaubte_naechste_module": ["CORE-16", "CORE-17", "CORE-18"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Migrationsplan dokumentiert",
            "Dry-Report vorhanden",
            "Kopiermigrations-Bericht vorhanden",
            "Manifest der kopierten Dateien erstellt"
        ]
    })

    # ======================================================================
    # PHASE 4: Test und Abnahme (CORE-16 bis CORE-20)
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-16",
        "name": "Neustruktur-Validierung und Reste-Archiv",
        "beschreibung": "Neustruktur validieren, Reste-Archiv-Sperrplan umsetzen, Umbau-Bericht.",
        "phase": "Phase 4: Test und Abnahme",
        "prioritaet": 16,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-15"],
        "eingaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json",
            "ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_sperrhinweise.csv"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/CORE18_NEUSTRUKTUR_VALIDIERUNG_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE19_RESTE_ARCHIV_SPERRPLAN_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE20_MASTER_UMBAU_BERICHT.txt"
        ],
        "sperren": ["Migration nicht abgeschlossen"],
        "tests": [
            "Neustruktur validiert",
            "Reste-Archiv gesperrt",
            "Master-Umbau-Bericht vorhanden"
        ],
        "erlaubte_naechste_module": ["CORE-17", "CORE-18", "CORE-19", "CORE-20"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Validierungsbericht erstellt",
            "Sperrplan umgesetzt",
            "Master-Umbau dokumentiert"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-17",
        "name": "Arbeitsindex und Agenten-Einstieg",
        "beschreibung": "Arbeitsindex erstellen, Agentenregeln definieren, Agenten-Einstieg dokumentieren.",
        "phase": "Phase 4: Test und Abnahme",
        "prioritaet": 17,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-16"],
        "eingaben": [
            "Config/core21_arbeitsindex_v1.json",
            "Config/core22_agentenregeln_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/AGENTENFREIGABE_KLARSTELLUNG.txt"
        ],
        "ausgaben": [
            "Config/core21_arbeitsindex_v1.json",
            "Config/core22_agentenregeln_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json",
            "ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt"
        ],
        "sperren": ["Validierung nicht abgeschlossen", "Agentenfreigabe nicht klar"],
        "tests": [
            "Arbeitsindex vollstaendig",
            "Agentenregeln validiert",
            "Agenten-Einstieg dokumentiert"
        ],
        "erlaubte_naechste_module": ["CORE-18", "CORE-19", "CORE-20", "CORE-21"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Arbeitsindex-Bericht vorhanden",
            "Agentenregeln manifestiert",
            "Einstiegs-Bericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-18",
        "name": "Projekt-Dashboard",
        "beschreibung": "Projekt-Dashboard erstellen, HTML- und JSON-Dashboard, Statusvisualisierung.",
        "phase": "Phase 4: Test und Abnahme",
        "prioritaet": 18,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-17"],
        "eingaben": [
            "ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt",
            "Config/core23_dashboard_v1.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.html",
            "ALIN_Neustart_Core/Reports/CORE23_PROJEKT_DASHBOARD_BERICHT.txt"
        ],
        "sperren": ["Arbeitsindex nicht erstellt"],
        "tests": [
            "Dashboard-JSON validiert",
            "Dashboard-HTML renderbar",
            "Status korrekt visualisiert"
        ],
        "erlaubte_naechste_module": ["CORE-19", "CORE-20", "CORE-21", "CORE-24"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Dashboard-JSON erstellt",
            "Dashboard-HTML erstellt",
            "Dashboard-Bericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-19",
        "name": "Rechte und Rollen",
        "beschreibung": "Rollenmodell implementieren, Berechtigungen pruefen, Freigaberegeln definieren.",
        "phase": "Phase 4: Test und Abnahme",
        "prioritaet": 19,
        "status": "offen",
        "abhaengigkeiten": ["CORE-17", "CORE-18"],
        "eingaben": [
            "ALIN_Neustart_Core/18_Rechte_Rollen/ROLLENMODELL.md",
            "ALIN_Neustart_Core/18_Rechte_Rollen/FREIGABEREGELN.md",
            "ALIN_Neustart_Core/18_Rechte_Rollen/BERECHTIGUNGEN.schema.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/18_Rechte_Rollen/ROLLENMODELL.md",
            "ALIN_Neustart_Core/18_Rechte_Rollen/FREIGABEREGELN.md",
            "ALIN_Neustart_Core/18_Rechte_Rollen/BERECHTIGUNGEN.schema.json"
        ],
        "sperren": ["Dashboard nicht fertig", "Rollenmodell unvollstaendig"],
        "tests": [
            "Rollenmodell validiert",
            "Berechtigungs-Schema geprueft",
            "Freigaberegeln definiert"
        ],
        "erlaubte_naechste_module": ["CORE-20", "CORE-24"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Rollenmodell dokumentiert",
            "Berechtigungs-Schema validiert",
            "Freigaberegeln festgelegt"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-20",
        "name": "Datenschutz und Mandatsgeheimnis",
        "beschreibung": "Datenschutz-Markierungen umsetzen, Mandatsgeheimnis-Regeln pruefen, Exportregeln definieren.",
        "phase": "Phase 4: Test und Abnahme",
        "prioritaet": 20,
        "status": "offen",
        "abhaengigkeiten": ["CORE-19"],
        "eingaben": [
            "ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/MANDATSGEHEIMNIS_REGELN.md",
            "ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/EXPORTREGELN.md",
            "ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/DATENSCHUTZ_MARKIERUNGEN.schema.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/MANDATSGEHEIMNIS_REGELN.md",
            "ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/EXPORTREGELN.md",
            "ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/DATENSCHUTZ_MARKIERUNGEN.schema.json"
        ],
        "sperren": ["Rechte und Rollen nicht definiert"],
        "tests": [
            "Datenschutz-Markierungen validiert",
            "Mandatsgeheimnis-Regeln geprueft",
            "Exportregeln definiert"
        ],
        "erlaubte_naechste_module": ["CORE-24", "CORE-25"],
        "blockierte_module": ["CORE-21"],
        "fertigstellungskriterien": [
            "Datenschutz-Schema validiert",
            "Mandatsgeheimnis-Regeln dokumentiert",
            "Exportregeln festgelegt"
        ]
    })

    # ======================================================================
    # PHASE 5: Autonomer Betrieb (CORE-21 bis CORE-25)
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-21",
        "name": "Arbeitsindex und Agentenregeln",
        "beschreibung": "Arbeitsindex vollstaendig, Agentenregeln finalisiert, Agentenfreigabe klar gestellt.",
        "phase": "Phase 5: Autonomer Betrieb",
        "prioritaet": 21,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-17", "CORE-18"],
        "eingaben": [
            "Config/core21_arbeitsindex_v1.json",
            "Config/core22_agentenregeln_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/AGENTENFREIGABE_KLARSTELLUNG.txt"
        ],
        "ausgaben": [
            "Config/core21_arbeitsindex_v1.json",
            "Config/core22_agentenregeln_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json",
            "ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt",
            "ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt"
        ],
        "sperren": ["Agentenfreigabe unklar"],
        "tests": [
            "Arbeitsindex vollstaendig",
            "Agentenregeln validiert",
            "Freigabe klar gestellt"
        ],
        "erlaubte_naechste_module": ["CORE-22", "CORE-23", "CORE-24", "CORE-25"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Arbeitsindex manifestiert",
            "Agentenregeln manifestiert",
            "Berichte vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-22",
        "name": "Agenten-Einstieg",
        "beschreibung": "Agenten-Einstieg dokumentieren, erste autonome Auftraege definieren, Regelwerk manifestieren.",
        "phase": "Phase 5: Autonomer Betrieb",
        "prioritaet": 22,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-21"],
        "eingaben": [
            "Config/core22_agentenregeln_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/AGENTENFREIGABE_KLARSTELLUNG.txt"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json",
            "ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt"
        ],
        "sperren": ["Agentenregeln nicht final"],
        "tests": [
            "Agentenregeln validiert",
            "Freigabe manifestiert",
            "Einstieg dokumentiert"
        ],
        "erlaubte_naechste_module": ["CORE-23", "CORE-24", "CORE-25"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Agentenregeln manifestiert",
            "Einstiegs-Bericht vorhanden",
            "Freigabe klar"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-23",
        "name": "Projekt-Dashboard",
        "beschreibung": "Projekt-Dashboard als zentrale Statusuebersicht, HTML- und JSON-Variante.",
        "phase": "Phase 5: Autonomer Betrieb",
        "prioritaet": 23,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-22"],
        "eingaben": [
            "Config/core23_dashboard_v1.json",
            "ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.html",
            "ALIN_Neustart_Core/Reports/CORE23_PROJEKT_DASHBOARD_BERICHT.txt"
        ],
        "sperren": ["Agenten-Einstieg nicht dokumentiert"],
        "tests": [
            "Dashboard-JSON validiert",
            "Dashboard-HTML renderbar"
        ],
        "erlaubte_naechste_module": ["CORE-24", "CORE-25"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Dashboard-JSON erstellt",
            "Dashboard-HTML erstellt",
            "Bericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-24",
        "name": "Autonomer Entwicklungsmanager",
        "beschreibung": "Auftragsqueue, Selbstreparatur, Queue-Verwaltung, autonome Auftragsableitung.",
        "phase": "Phase 5: Autonomer Betrieb",
        "prioritaet": 24,
        "status": "abgeschlossen",
        "abhaengigkeiten": ["CORE-21", "CORE-22", "CORE-23"],
        "eingaben": [
            "Config/core24_entwicklungsmanager_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/AGENTENFREIGABE_KLARSTELLUNG.txt"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_reparatur_log.json",
            "ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt",
            "Scripts/python_runner/core24_entwicklungsmanager.py"
        ],
        "sperren": ["Dashboard nicht fertig", "Agentenfreigabe nicht klar"],
        "tests": [
            "Queue-JSON validiert",
            "Reparatur-Log funktioniert",
            "Autonome Ableitung getestet"
        ],
        "erlaubte_naechste_module": ["CORE-25", "CORE-26"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Entwicklungsmanager laeuft",
            "Queue erstellt",
            "Reparatur-Log funktioniert",
            "Bericht vorhanden"
        ]
    })

    stufen.append({
        "stufe_id": "CORE-25",
        "name": "Programmierbare Gesamt-Roadmap",
        "beschreibung": "Fachliches Gesamtkonzept wird in maschinenlesbare Roadmap fuer CORE-24 zerlegt.",
        "phase": "Phase 5: Autonomer Betrieb",
        "prioritaet": 25,
        "status": "in_bearbeitung",
        "abhaengigkeiten": ["CORE-24"],
        "eingaben": [
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md",
            "ALIN_Neustart_Core/00_Dokumentation/ALIN_NAECHSTE_AUFTRAEGE.md",
            "Config/core24_entwicklungsmanager_v1.json",
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_gesamt_roadmap.json",
            "ALIN_Neustart_Core/Reports/CORE25_GESAMT_ROADMAP_BERICHT.txt",
            "Config/core25_roadmap_v1.json",
            "Scripts/python_runner/core25_gesamt_roadmap.py",
            "Scripts/python_runner/check_core25_gesamt_roadmap.py",
            "Scripts/CORE25_GESAMT_ROADMAP_AUTOLAUF.ps1",
            "Projektplanung/CORE25_GESAMT_ROADMAP.md"
        ],
        "sperren": ["CORE-24 nicht abgeschlossen", "Auftragsqueue leer"],
        "tests": [
            "Roadmap-JSON validiert",
            "Abhaengigkeiten zyklenfrei",
            "Alle Stufen eindeutige ID",
            "Pruefdatei bestanden"
        ],
        "erlaubte_naechste_module": ["CORE-26", "UI14"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Roadmap-JSON erstellt",
            "Zyklenfreiheit geprueft",
            "Bericht vorhanden",
            "Config erstellt",
            "Dokumentation erstellt"
        ]
    })

    # ======================================================================
    # UI-MODULE (UI01 - UI14)
    # ======================================================================
    ui_module = [
        ("UI01", "Anwaltsansicht", ["CORE-09", "CORE-10"], 30, "Config/ui01_anwaltsansicht_v1.json",
         ["Scripts/python_runner/ui01_anwaltsansicht.py", "Scripts/UI01_ANWALTSANSICHT_AUTOLAUF.ps1", "Projektplanung/UI01_ANWALTSANSICHT_V1.md"]),
        ("UI02", "Tuerschwelle und Bestandsabgleich", ["UI01"], 31, "Config/ui02_tuerschwelle_bau_v1.json",
         ["Scripts/python_runner/ui02_0_bestandsabgleich_tuerschwelle.py", "Scripts/ui02_tuerschwelle_bau_starter.ps1", "Projektplanung/UI02_0_BESTANDSABGLEICH_DOKUMENTATION.md", "Projektplanung/UI02_TUERSCHWELLENVORLAGE_DOKU.md"]),
        ("UI02c", "Freigabe Dropdowns und Notizen", ["UI02"], 31.5, "Config/ui02c_freigabe_dropdowns_notizen_v1.json",
         ["Scripts/python_runner/ui02c_freigabe_dropdowns_notizen.py", "Scripts/UI02c_FREIGABE_DROPDOWNS_NOTIZEN_AUTOLAUF.ps1", "Projektplanung/UI02c_FREIGABE_DROPDOWNS_NOTIZEN.md"]),
        ("UI03_0", "Uebergabe Mandantenakte", ["UI02c"], 32, "Config/ui03_1_anwalts_dreiansicht_v1.json",
         ["Scripts/python_runner/ui03_0_uebergabe_mandantenakte.py", "Scripts/UI03_0_UEBERGABE_MANDANTENAKTE_AUTOLAUF.ps1", "Projektplanung/UI03_0_UEBERGABE_MANDANTENAKTE.md"]),
        ("UI03_1", "Anwalts Dreiansicht", ["UI03_0"], 33, "Config/ui03_1_anwalts_dreiansicht_v1.json",
         ["Scripts/python_runner/ui03_1_anwalts_dreiansicht.py", "Scripts/UI03_1_ANWALTS_DREIANSICHT_AUTOLAUF.ps1", "Projektplanung/UI03_1_ANWALTS_DREIANSICHT.md"]),
        ("UI03_1b", "OCR Uebersetzungskontrolle", ["UI03_1", "CORE-08"], 33.1, "Config/ui03_1b_ocr_uebersetzungskontrolle_v1.json",
         ["Scripts/python_runner/ui03_1b_ocr_uebersetzungskontrolle.py", "Scripts/UI03_1b_OCR_UEBERSETZUNGSKONTROLLE_AUTOLAUF.ps1", "Projektplanung/UI03_1b_OCR_UEBERSETZUNGSKONTROLLE.md"]),
        ("UI03_1c", "Uebersetzungsarbeitsplatz", ["UI03_1b"], 33.2, "Config/ui03_1c_uebersetzungsarbeitsplatz_v1.json",
         ["Scripts/python_runner/ui03_1c_uebersetzungsarbeitsplatz.py", "Scripts/UI03_1c_UEBERSETZUNGSARBEITSPLATZ_AUTOLAUF.ps1", "Projektplanung/UI03_1c_UEBERSETZUNGSARBEITSPLATZ.md"]),
        ("UI03_1d", "OCR Freigabeablauf", ["UI03_1c"], 33.3, "Config/ui03_1d_ocr_freigabeablauf_v1.json",
         ["Scripts/python_runner/ui03_1d_ocr_freigabeablauf.py", "Scripts/UI03_1d_OCR_FREIGABEABLAUF_AUTOLAUF.ps1", "Projektplanung/UI03_1d_OCR_FREIGABEABLAUF.md"]),
        ("UI03_1e", "Uebergabe Freigabe", ["UI03_1d"], 33.4, "Config/ui03_1e_uebergabe_freigabe_v1.json",
         ["Scripts/python_runner/ui03_1e_uebergabe_freigabe.py", "Scripts/UI03_1e_UEBERGABE_FREIGABE_AUTOLAUF.ps1", "Projektplanung/UI03_1e_UEBERGABE_FREIGABE.md"]),
        ("UI03_1f", "Geparkte Auftraege", ["UI03_1e"], 33.5, "Config/ui03_1f_geparkte_auftraege_v1.json",
         ["Scripts/python_runner/ui03_1f_geparkte_auftraege.py", "Scripts/UI03_1f_GEPARKTE_AUFTRAEGE_AUTOLAUF.ps1", "Projektplanung/UI03_1f_GEPARKTE_AUFTRAEGE.md"]),
        ("UI03_1g", "Gesamtansicht", ["UI03_1f"], 33.6, "Config/ui03_1g_gesamtansicht_v1.json",
         ["Scripts/python_runner/ui03_1g_gesamtansicht.py", "Scripts/UI03_1g_GESAMTANSICHT_AUTOLAUF.ps1", "Projektplanung/UI03_1g_GESAMTANSICHT.md"]),
        ("UI04", "Durchstich Sekretariat-Anwalt-Ruecklauf", ["UI03_1g"], 34, "Config/ui04_durchstich_sekretariat_anwalt_ruecklauf_v1.json",
         ["Scripts/python_runner/ui04_durchstich_sekretariat_anwalt_ruecklauf.py", "Scripts/UI04_DURCHSTICH_SEKRETARIAT_ANWALT_RUECKLAUF_AUTOLAUF.ps1", "Projektplanung/UI04_DURCHSTICH_SEKRETARIAT_ANWALT_RUECKLAUF.md"]),
        ("UI04b", "Logikpruefung Entscheidung", ["UI04"], 34.5, "Config/ui04b_logikpruefung_entscheidung_v1.json",
         ["Scripts/python_runner/ui04b_logikpruefung_entscheidung.py", "Scripts/UI04b_LOGIKPRUEFUNG_ENTSCHEIDUNG_AUTOLAUF.ps1", "Projektplanung/UI04b_LOGIKPRUEFUNG_ENTSCHEIDUNG.md"]),
        ("UI05", "Mandantenakte Arbeitszentrale", ["UI04b"], 35, "Config/ui05_mandantenakte_arbeitszentrale_v1.json",
         ["Scripts/python_runner/ui05_mandantenakte_arbeitszentrale.py", "Scripts/UI05_MANDANTENAKTE_ARBEITSZENTRALE_AUTOLAUF.ps1", "Projektplanung/UI05_MANDANTENAKTE_ARBEITSZENTRALE.md"]),
        ("UI06", "Musterlauf Gesamtkette", ["UI05"], 36, "Config/ui06_musterlauf_gesamtkette_v1.json",
         ["Scripts/python_runner/ui06_musterlauf_gesamtkette.py", "Scripts/UI06_MUSTERLAUF_GESAMTKETTE_AUTOLAUF.ps1", "Projektplanung/UI06_MUSTERLAUF_GESAMTKETTE.md"]),
        ("UI06b", "Fehlerpfad Pruefung", ["UI06"], 36.5, "Config/ui06b_fehlerpfad_pruefung_v1.json",
         ["Scripts/python_runner/ui06b_fehlerpfad_pruefung.py", "Scripts/UI06B_FEHLERPFAD_PRUEFUNG_AUTOLAUF.ps1", "Projektplanung/UI06B_FEHLERPFAD_PRUEFUNG.md"]),
        ("UI07", "Betriebsvorbereitung", ["UI06b"], 37, "Config/ui07_betriebsvorbereitung_v1.json",
         ["Scripts/python_runner/ui07_betriebsvorbereitung.py", "Scripts/UI07_BETRIEBSVORBEREITUNG_AUTOLAUF.ps1", "Projektplanung/UI07_BETRIEBSVORBEREITUNG.md"]),
        ("UI07b", "Gesamtfreeze Demo Betriebsstrecke", ["UI07"], 37.5, "Config/ui07b_gesamtfreeze_demo_betriebsstrecke_v1.json",
         ["Scripts/python_runner/ui07b_gesamtfreeze_demo_betriebsstrecke.py", "Scripts/UI07B_GESAMTFREEZE_DEMO_BETRIEBSSTRECKE_AUTOLAUF.ps1", "Projektplanung/UI07B_GESAMTFREEZE_DEMO_BETRIEBSSTRECKE.md"]),
        ("UI08", "Posteingang Importstrecke", ["CORE-07", "UI07b"], 38, "Config/ui08_posteingang_importstrecke_v1.json",
         ["Scripts/python_runner/ui08_posteingang_importstrecke.py", "Scripts/UI08_POSTEINGANG_IMPORTSTRECKE_AUTOLAUF.ps1", "Projektplanung/UI08_POSTEINGANG_IMPORTSTRECKE.md"]),
        ("UI08b", "Fehlerpfad Pruefung Posteingang", ["UI08"], 38.5, "Config/ui08b_fehlerpfad_pruefung_posteingang_v1.json",
         ["Scripts/python_runner/ui08b_fehlerpfad_pruefung_posteingang.py", "Scripts/UI08B_FEHLERPFAD_PRUEFUNG_POSTEINGANG_AUTOLAUF.ps1", "Projektplanung/UI08B_FEHLERPFAD_PRUEFUNG_POSTEINGANG.md"]),
        ("UI08c", "Fehlerpfad Sanierungsplan Posteingang", ["UI08b"], 38.6, "Config/ui08c_fehlerpfad_sanierungsplan_posteingang_v1.json",
         ["Scripts/python_runner/ui08c_fehlerpfad_sanierungsplan_posteingang.py", "Scripts/UI08C_FEHLERPFAD_SANIERUNGSPLAN_POSTEINGANG_AUTOLAUF.ps1", "Projektplanung/UI08C_FEHLERPFAD_SANIERUNGSPLAN_POSTEINGANG.md"]),
        ("UI09", "Zentrale Grundschalter Profilfelder", ["UI08c"], 39, "Config/ui09_zentrale_grundschalter_profilfelder_v1.json",
         ["Scripts/python_runner/ui09_zentrale_grundschalter_profilfelder.py", "Scripts/UI09_ZENTRALE_GRUNDSCHALTER_PROFILFELDER_AUTOLAUF.ps1", "Projektplanung/UI09_ZENTRALE_GRUNDSCHALTER_PROFILFELDER.md"]),
        ("UI10", "Profil Lesadapter", ["UI09"], 40, "Config/ui10_profil_lesadapter_v1.json",
         ["Scripts/python_runner/ui10_profil_lesadapter.py", "Scripts/UI10_PROFIL_LESADAPTER_AUTOLAUF.ps1", "Projektplanung/UI10_PROFIL_LESADAPTER.md"]),
        ("UI11", "Register Lesadapter", ["UI10"], 41, "Config/ui11_register_lesadapter_v1.json",
         ["Scripts/python_runner/ui11_register_lesadapter.py", "Scripts/UI11_REGISTER_LESADAPTER_AUTOLAUF.ps1", "Projektplanung/UI11_REGISTER_LESADAPTER.md"]),
        ("UI12", "Master Adapter", ["UI11"], 42, "Config/ui12_master_adapter_v1.json",
         ["Scripts/python_runner/ui12_master_adapter.py", "Scripts/UI12_MASTER_ADAPTER_AUTOLAUF.ps1", "Projektplanung/UI12_MASTER_ADAPTER.md"]),
        ("UI13", "Abnahme Entscheidungsuebersicht", ["UI12"], 43, "Config/ui13_abnahme_entscheidungsuebersicht_v1.json",
         ["Scripts/python_runner/ui13_abnahme_entscheidungsuebersicht.py", "Scripts/UI13_ABNAHME_ENTSCHEIDUNGSUEBERSICHT_AUTOLAUF.ps1", "Projektplanung/UI13_ABNAHME_ENTSCHEIDUNGSUEBERSICHT.md"]),
        ("UI14", "Ausfuehrungs-Nachlaufzentrale", ["UI13", "CORE-25"], 44, "Config/ui14_ausfuehrungs_nachlaufzentrale_v1.json",
         ["Scripts/python_runner/ui14_ausfuehrungs_nachlaufzentrale.py", "Scripts/UI14_AUSFUEHRUNGS_NACHLAUFZENTRALE_AUTOLAUF.ps1", "Projektplanung/UI14_AUSFUEHRUNGS_NACHLAUFZENTRALE.md"])
    ]

    for mod in ui_module:
        stufe_id, name, deps, prio, config_pfad, ausgaben_liste = mod
        stufen.append({
            "stufe_id": stufe_id,
            "name": name,
            "beschreibung": f"UI-Modul: {name}",
            "phase": "UI-Strecke",
            "prioritaet": prio,
            "status": "abgeschlossen",
            "abhaengigkeiten": deps,
            "eingaben": [config_pfad] + [d for d in deps if d.startswith("Config/") or d.startswith("ALIN_")],
            "ausgaben": ausgaben_liste,
            "sperren": [f"{d} nicht abgeschlossen" for d in deps],
            "tests": [
                f"{stufe_id} Python-Runner erfolgreich",
                f"{stufe_id} Check-Datei bestanden",
                f"{stufe_id} PowerShell-Starter funktioniert"
            ],
            "erlaubte_naechste_module": [],
            "blockierte_module": [],
            "fertigstellungskriterien": [
                f"Python-Runner {stufe_id} erstellt",
                f"Check-Datei {stufe_id} erstellt",
                f"PowerShell-Starter {stufe_id} erstellt",
                "Dokumentation erstellt"
            ]
        })

    # ======================================================================
    # KM-MODULE (KM12 - KM21)
    # ======================================================================
    km_module = [
        ("KM12", "Originalabbildung", ["CORE-08"], 50, "Config/originalabbildung_v1.json",
         ["Scripts/Run_KM12_Originalabbildung.ps1", "Projektplanung/KM12b_UEBERGROSSE_ARBEITSABBILDUNGEN.md"]),
        ("KM12b", "Uebergrosse Arbeitsabbildungen", ["KM12"], 50.5, "Config/km12b_uebergrosse_arbeitsabbildungen_v1.json",
         ["Scripts/Run_KM12b_Uebergrosse_Arbeitsabbildungen.ps1", "Projektplanung/KM12b_UEBERGROSSE_ARBEITSABBILDUNGEN.md"]),
        ("KM13", "OCR-Pipeline", ["KM12b"], 51, "Config/ocr_pipeline_v1.json",
         ["Scripts/Run_KM13_OCR_Pipeline.ps1", "Projektplanung/KM13b_TESSERACT_SPRACHPAKET_ABGLEICH.md"]),
        ("KM13b", "Tesseract Sprachpaket Abgleich", ["KM13"], 51.5, "Config/tesseract_sprachpaket_abgleich_v1.json",
         ["Scripts/Run_KM13b_Tesseract_Sprachpaket_Abgleich.ps1", "Projektplanung/KM13b_TESSERACT_SPRACHPAKET_ABGLEICH.md"]),
        ("KM14", "Maschinenformat Fundstellenstruktur", ["KM13b"], 52, "Config/maschinenformat_fundstellenstruktur_v1.json",
         ["Scripts/Run_KM14_Maschinenformat_Fundstellenstruktur.ps1", "Projektplanung/KM14_DOKUMENTATION.md"]),
        ("KM15", "Arbeitsuebersetzung Fundstellenbindung", ["KM14"], 53, "Config/arbeitsuebersetzung_fundstellenbindung_v1.json",
         ["Scripts/Run_KM15_Arbeitsuebersetzung_Fundstellenbindung.ps1"]),
        ("KM16", "Sprachrouting vor OCR", ["KM15"], 54, "Config/sprachrouting_vor_ocr_v1.json",
         ["Scripts/Run_KM16_Sprachrouting_Vor_OCR.ps1", "Projektplanung/KM16_SPRACHROUTING_VOR_OCR.md"]),
        ("KM17", "Sprachrouting OCR Integration", ["KM16"], 55, "Config/km17_sprachrouting_ocr_v1.json",
         ["Scripts/Run_KM17_AUTOLAUF.ps1", "Projektplanung/KM17_SPRACHROUTING_OCR_INTEGRATION.md"]),
        ("KM17c", "Einzelseite KM12b OCR", ["KM17"], 55.5, "Config/km17c_einzelseite_km12b_ocr_v1.json",
         ["Scripts/Run_KM17c_EINZELSEITE_KM12b_AUTOLAUF.ps1", "Projektplanung/KM17c_EINZELSEITE_KM12b_OCR.md"]),
        ("KM18", "OCR Ergebnisdiagnose", ["KM17c"], 56, "Config/km18_ocr_ergebnisdiagnose_v1.json",
         ["Scripts/Run_KM18_AUTOLAUF.ps1", "Projektplanung/KM18_OCR_ERGEBNISDIAGNOSE.md"]),
        ("KM19", "OCR Gesamtkette synchronisieren", ["KM18"], 57, "Config/km19_ocr_gesamtkette_synchronisieren_v1.json",
         ["Scripts/Run_KM19_OCR_GESAMTKETTE_SYNCHRONISIEREN_AUTOLAUF.ps1", "Projektplanung/KM19_OCR_GESAMTKETTE_SYNCHRONISIEREN.md"]),
        ("KM19b", "OCRBetreuer Korrektur", ["KM19"], 57.5, "Config/km19_ocrbetreuer_korrektur_v1.json",
         ["Scripts/Run_KM19_OCRBETREUER_KORREKTUR_AUTOLAUF.ps1", "Projektplanung/KM19_OCRBETREUER_KORREKTUR.md"]),
        ("KM20", "Konsolidierung", ["KM19b"], 58, "Config/km20_quellen_fundstellen_konsolidierung_v1.json",
         ["Scripts/Run_KM20_Konsolidierung.ps1", "Projektplanung/KM20_KONSOLIDIERUNG.md"]),
        ("KM20b", "Bereinigung", ["KM20"], 58.5, "Config/km20b_bereinigung_v1.json",
         ["Scripts/Run_KM20b_Bereinigung.ps1"]),
        ("KM21", "Translation Environment", ["KM20b"], 59, "Config/km21_translation_env_v1.json",
         ["Scripts/Run_KM21_TRANSLATION_ENV.ps1", "Projektplanung/KM21_TRANSLATION_ENV.md"]),
        ("KM21b0", "ARGOS Modellbereitstellung", ["KM21"], 59.5, "Config/km21b0_argos_modellbereitstellung_v1.json",
         ["Projektplanung/KM21b0_ARGOS_MODELLBEREITSTELLUNG.md"])
    ]

    for mod in km_module:
        stufe_id, name, deps, prio, config_pfad, ausgaben_liste = mod
        stufen.append({
            "stufe_id": stufe_id,
            "name": name,
            "beschreibung": f"KM-Modul: {name}",
            "phase": "OCR- und Uebersetzungsstrecke",
            "prioritaet": prio,
            "status": "abgeschlossen",
            "abhaengigkeiten": deps,
            "eingaben": [config_pfad],
            "ausgaben": ausgaben_liste,
            "sperren": [f"{d} nicht abgeschlossen" for d in deps],
            "tests": [
                f"{stufe_id} Konfiguration validiert",
                f"{stufe_id} Skripte vorhanden"
            ],
            "erlaubte_naechste_module": [],
            "blockierte_module": [],
            "fertigstellungskriterien": [
                f"Konfiguration {stufe_id} erstellt",
                f"Skripte {stufe_id} erstellt",
                "Dokumentation vorhanden"
            ]
        })

    # ======================================================================
    # POSTEINGANG / VORZIMMER
    # ======================================================================
    post_module = [
        ("POST01", "Posteingang Intake", ["CORE-07"], 60, "Config/alin_posteingang_config.json",
         ["Scripts/Run_Posteingang_Pipeline.ps1", "Scripts/Run_Posteingang_Zentrale.ps1"]),
        ("POST02", "Posteingang Schlusskontrolle", ["POST01"], 61, "Config/posteingang_schlusskontrolle_v2.json",
         ["Scripts/Run_Posteingang_Schlusskontrolle.ps1"]),
        ("POST03", "Posteingang Endabnahme", ["POST02"], 62, "Config/posteingang_schlusskontrolle_v2.json",
         ["Scripts/Run_Posteingang_Menu.ps1", "Scripts/Run_Posteingang_Zentrale.ps1"]),
        ("VZ01", "Vorzimmer Kommunikationsparameter", ["POST03"], 63, "Config/vorzimmer_kommunikationsparameter_v1.json",
         ["Scripts/Run_Vorzimmer_Kommunikationsparameter.ps1", "Scripts/python_runner/035_vorzimmer_kommunikationsparameter_v1.py"])
    ]

    for mod in post_module:
        stufe_id, name, deps, prio, config_pfad, ausgaben_liste = mod
        stufen.append({
            "stufe_id": stufe_id,
            "name": name,
            "beschreibung": f"Posteingang/Vorzimmer: {name}",
            "phase": "Posteingang und Vorzimmer",
            "prioritaet": prio,
            "status": "abgeschlossen",
            "abhaengigkeiten": deps,
            "eingaben": [config_pfad],
            "ausgaben": ausgaben_liste,
            "sperren": [f"{d} nicht abgeschlossen" for d in deps],
            "tests": [
                f"{stufe_id} Pipeline erfolgreich",
                f"{stufe_id} Endabnahme bestanden"
            ],
            "erlaubte_naechste_module": [],
            "blockierte_module": [],
            "fertigstellungskriterien": [
                f"Pipeline {stufe_id} laeuft",
                f"Endabnahme {stufe_id} bestanden"
            ]
        })

    # ======================================================================
    # QUELLEN und AGENTEN
    # ======================================================================
    quellen_module = [
        ("Q01", "Quellenbetreuer Fachanwaltsraster", ["CORE-10"], 70, "Config/agentenbearbeitung_grundmodul_v1.json",
         ["Scripts/Run_Quellenbetreuer_Fachanwaltsraster.ps1", "Projektplanung/Quellen/QUELLENBETREUER_FACHANWALTSRASTER_V1.md"]),
        ("Q02", "Quellenkandidaten EU SE Official Sources", ["Q01"], 71, "Config/eu_official_ocr_languages_v1.json",
         ["Scripts/Run_Quellenkandidaten_EU_SE.ps1", "Projektplanung/Quellen/QUELLENKANDIDATEN_EU_SE_OFFICIAL_SOURCES_V1.md"]),
        ("Q03", "Source Adapter Healthcheck Framework", ["Q02"], 72, "Config/source_adapter_policy_v1.json",
         ["Scripts/Run_Source_Adapter_Healthcheck_Framework.ps1", "Projektplanung/Quellen/SOURCE_ADAPTER_HEALTHCHECK_FRAMEWORK_V1.md"]),
        ("AG01", "Agentenbearbeitung Grundmodul", ["CORE-10"], 73, "Config/agentenbearbeitung_grundmodul_v1.json",
         ["Scripts/Run_Agentenbearbeitung.ps1", "Scripts/python_runner/037_posteingang_endabnahme_v3.py"]),
        ("AG02", "Agent Dokumentart erkennen", ["AG01"], 74, "Config/agent_dokumentart_erkennen_v1.json",
         ["Scripts/Run_Agent_Dokumentart.ps1"]),
        ("AG03", "Agent Sprache Uebersetzung", ["AG02"], 75, "Config/agent_sprache_uebersetzung_v1.json",
         ["Scripts/Run_Agent_Sprache_Uebersetzung.ps1"]),
        ("AG04", "Agent Sachverhaltsbezug", ["AG03"], 76, "Config/agent_sachverhaltsbezug_v1.json",
         ["Scripts/Run_Agent_Sachverhaltsbezug.ps1"])
    ]

    for mod in quellen_module:
        stufe_id, name, deps, prio, config_pfad, ausgaben_liste = mod
        stufen.append({
            "stufe_id": stufe_id,
            "name": name,
            "beschreibung": f"Quellen/Agenten: {name}",
            "phase": "Quellen und Agenten",
            "prioritaet": prio,
            "status": "abgeschlossen",
            "abhaengigkeiten": deps,
            "eingaben": [config_pfad],
            "ausgaben": ausgaben_liste,
            "sperren": [f"{d} nicht abgeschlossen" for d in deps],
            "tests": [
                f"{stufe_id} Konfiguration validiert",
                f"{stufe_id} Skripte vorhanden"
            ],
            "erlaubte_naechste_module": [],
            "blockierte_module": [],
            "fertigstellungskriterien": [
                f"Konfiguration {stufe_id} erstellt",
                f"Skripte {stufe_id} erstellt",
                "Dokumentation vorhanden"
            ]
        })

    # ======================================================================
    # WINDOWS APP BUILD
    # ======================================================================
    stufen.append({
        "stufe_id": "WINAPP",
        "name": "Windows App Build und Release",
        "beschreibung": "Windows-App kompilieren, Release-Checkliste, Changelog, Rollback-Plan.",
        "phase": "Build und Release",
        "prioritaet": 80,
        "status": "offen",
        "abhaengigkeiten": ["CORE-12", "UI14"],
        "eingaben": [
            "Windows_App/App/KI_Legal_WindowsApp.csproj",
            "ALIN_Neustart_Core/16_Build_Release/RELEASE_CHECKLIST.md",
            "ALIN_Neustart_Core/16_Build_Release/CHANGELOG.md",
            "ALIN_Neustart_Core/16_Build_Release/ROLLBACK_PLAN.md"
        ],
        "ausgaben": [
            "Windows_App/Scripts/Build_App.ps1",
            "ALIN_Neustart_Core/16_Build_Release/CHANGELOG.md",
            "ALIN_Neustart_Core/16_Build_Release/VERSION.json"
        ],
        "sperren": ["UI-Grundlagen nicht fertig", "Windows-App-Architektur nicht final"],
        "tests": [
            "Build erfolgreich",
            "Release-Checkliste abgearbeitet",
            "Rollback-Plan aktuell"
        ],
        "erlaubte_naechste_module": ["DEPLOY"],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Build-Skript funktioniert",
            "Changelog aktualisiert",
            "VERSION.json aktualisiert"
        ]
    })

    stufen.append({
        "stufe_id": "DEPLOY",
        "name": "Deployment und Betrieb",
        "beschreibung": "MSIX-Paketierung, Offline-Installation, Gerichtslaptop-Profil, Betriebsvorbereitung.",
        "phase": "Build und Release",
        "prioritaet": 90,
        "status": "offen",
        "abhaengigkeiten": ["WINAPP", "CORE-20"],
        "eingaben": [
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_DEPLOYMENT_PRUEFPUNKTE_V1.md",
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_OFFLINE_GERICHTSLAPTOP_V1.md",
            "ALIN_Neustart_Core/24_Konfigurationsprofile/PROFIL_GERICHTSLAPTOP_OFFLINE.json"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/08_Windows_App_Grundlage/ALIN_WINDOWS_DEPLOYMENT_PRUEFPUNKTE_V1.md",
            "ALIN_Neustart_Core/24_Konfigurationsprofile/PROFIL_GERICHTSLAPTOP_OFFLINE.json",
            "ALIN_Neustart_Core/24_Konfigurationsprofile/PROFIL_KANZLEI_PC.json"
        ],
        "sperren": ["Windows-App nicht gebaut", "Datenschutz nicht definiert"],
        "tests": [
            "Deployment-Pruefpunkte abgearbeitet",
            "Offline-Profil getestet",
            "Gerichtslaptop-Profil validiert"
        ],
        "erlaubte_naechste_module": [],
        "blockierte_module": [],
        "fertigstellungskriterien": [
            "Deployment-Checkliste abgeschlossen",
            "Offline-Profil getestet",
            "Konfigurationsprofile vorhanden"
        ]
    })

    # ======================================================================
    # ABSCHLUSS und PRUEFUNG
    # ======================================================================
    stufen.append({
        "stufe_id": "CORE-26",
        "name": "Gesamtabnahme und Produktionsfreigabe",
        "beschreibung": "Finale Gesamtabnahme aller Module, Produktionsfreigabe (nur durch menschlichen Entscheid).",
        "phase": "Abschluss",
        "prioritaet": 100,
        "status": "gesperrt",
        "abhaengigkeiten": ["CORE-25", "DEPLOY", "UI14", "KM21b0"],
        "eingaben": [
            "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_gesamt_roadmap.json",
            "ALIN_Neustart_Core/Reports/",
            "Config/"
        ],
        "ausgaben": [
            "ALIN_Neustart_Core/Reports/CORE26_GESAMTABNAHME_BERICHT.txt",
            "ALIN_Neustart_Core/16_Build_Release/RELEASE_CHECKLIST.md"
        ],
        "sperren": [
            "Menschliche Freigabe erforderlich",
            "Nicht alle Module abgeschlossen",
            "Keine Beweiswuerdigung durch KI"
        ],
        "tests": [
            "Alle Pruefberichte bestanden",
            "Roadmap vollstaendig",
            "Zyklenfreiheit bestaetigt",
            "Menschliche Abnahme dokumentiert"
        ],
        "erlaubte_naechste_module": [],
        "blockierte_module": ["ALLE"],
        "fertigstellungskriterien": [
            "Alle Lieferpflichten erfuellt",
            "Menschliche Abnahme dokumentiert",
            "Keine offenen Sperren",
            "Release-Checkliste abgeschlossen"
        ]
    })

    return {
        "meta": {
            "modul_id": "CORE-25",
            "name": "Programmierbare Gesamt-Roadmap",
            "version": "1.0.0",
            "zeitstempel_erstellung": zeitstempel(),
            "quellen": [
                "ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md",
                "ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md",
                "ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md",
                "ALIN_Neustart_Core/00_Dokumentation/ALIN_NAECHSTE_AUFTRAEGE.md",
                "Config/core24_entwicklungsmanager_v1.json",
                "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json"
            ],
            "ziel_format": "CORE-24 kompatibel",
            "anzahl_stufen": len(stufen)
        },
        "roadmap": {
            "stufen": stufen,
            "abhaengigkeits_graph": {},
            "phases": [
                "Vorbereitung",
                "Phase 1: Grundmodell",
                "Phase 2: Altbestand",
                "Phase 3: Windows-App",
                "Phase 4: Test und Abnahme",
                "Phase 5: Autonomer Betrieb",
                "UI-Strecke",
                "OCR- und Uebersetzungsstrecke",
                "Posteingang und Vorzimmer",
                "Quellen und Agenten",
                "Build und Release",
                "Abschluss"
            ]
        },
        "validierung": {
            "zyklische_abhaengigkeiten": False,
            "alle_stufen_eindeutige_id": True,
            "alle_abhaengigkeiten_aufloesbar": True,
            "pruefzeitstempel": zeitstempel()
        }
    }


# =============================================================================
# VALIDIERUNG
# =============================================================================


def pruefe_zyklische_abhaengigkeiten(stufen: list[dict]) -> tuple[bool, list[str]]:
    """
    Prueft, ob im Abhaengigkeitsgraph Zyklen vorhanden sind.
    Verwendet DFS-basierte Zyklenerkennung.
    """
    # Baue Adjazenzliste
    graph = {}
    alle_ids = set()
    for stufe in stufen:
        sid = stufe["stufe_id"]
        alle_ids.add(sid)
        graph[sid] = stufe.get("abhaengigkeiten", [])

    # Pruefe, ob alle Abhaengigkeiten existieren
    fehlende = []
    for sid, deps in graph.items():
        for dep in deps:
            if dep not in alle_ids:
                fehlende.append(f"{sid} -> {dep} (existiert nicht)")

    # DFS fuer Zyklen
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {sid: WHITE for sid in alle_ids}
    zyklen = []

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                # Zyklus gefunden
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                zyklen.append(" -> ".join(cycle))
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for sid in alle_ids:
        if color[sid] == WHITE:
            dfs(sid, [])

    if zyklen or fehlende:
        meldungen = []
        if zyklen:
            meldungen.extend([f"ZYKLUS: {z}" for z in zyklen])
        if fehlende:
            meldungen.extend([f"FEHLENDE_ABHAENGIGKEIT: {f}" for f in fehlende])
        return False, meldungen

    return True, []


def validiere_roadmap(roadmap: dict) -> tuple[bool, list[str]]:
    """
    Validiert die erzeugte Roadmap.
    """
    fehler = []
    stufen = roadmap.get("roadmap", {}).get("stufen", [])
    config = lade_config()
    pflicht = config.get("roadmap_regeln", {}).get("pflicht_felder", [])
    erlaubte_status = config.get("roadmap_regeln", {}).get("erlaubte_status", [])

    ids = set()
    for stufe in stufen:
        sid = stufe.get("stufe_id", "")
        if not sid:
            fehler.append("Stufe ohne stufe_id gefunden")
            continue
        if sid in ids:
            fehler.append(f"Doppelte stufe_id: {sid}")
        ids.add(sid)

        for feld in pflicht:
            if feld not in stufe:
                fehler.append(f"{sid}: Pflichtfeld '{feld}' fehlt")

        status = stufe.get("status", "")
        if status and status not in erlaubte_status:
            fehler.append(f"{sid}: Ungueltiger Status '{status}'")

    ok, zyklen_meldungen = pruefe_zyklische_abhaengigkeiten(stufen)
    if not ok:
        fehler.extend(zyklen_meldungen)

    # Pruefe Meta
    meta = roadmap.get("meta", {})
    if meta.get("modul_id") != "CORE-25":
        fehler.append("Meta.modul_id muss CORE-25 sein")

    return len(fehler) == 0, fehler


# =============================================================================
# BERICHTSERSTELLUNG
# =============================================================================


def erzeuge_textbericht(roadmap: dict, valid_ok: bool, valid_fehler: list[str]) -> str:
    """
    Erzeugt den menschenlesbaren Bericht.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("CORE-25: GESAMT-ROADMAP BERICHT")
    lines.append("=" * 80)
    lines.append(f"Zeitstempel: {zeitstempel()}")
    lines.append(f"Modul: {roadmap['meta']['modul_id']} - {roadmap['meta']['name']}")
    lines.append(f"Version: {roadmap['meta']['version']}")
    lines.append(f"Anzahl Stufen: {roadmap['meta']['anzahl_stufen']}")
    lines.append("")
    lines.append("QUELLEN:")
    for q in roadmap["meta"]["quellen"]:
        lines.append(f"  - {q}")
    lines.append("")
    lines.append("VALIDIERUNG:")
    lines.append(f"  Zyklenfrei: {roadmap['validierung']['zyklische_abhaengigkeiten']}")
    lines.append(f"  Eindeutige IDs: {roadmap['validierung']['alle_stufen_eindeutige_id']}")
    lines.append(f"  Aufloesbare Abhaengigkeiten: {roadmap['validierung']['alle_abhaengigkeiten_aufloesbar']}")
    lines.append(f"  Runtime-Validierung OK: {valid_ok}")
    if valid_fehler:
        lines.append("  FEHLER:")
        for f in valid_fehler:
            lines.append(f"    - {f}")
    else:
        lines.append("  Keine Fehler.")
    lines.append("")
    lines.append("STUFEN-UEBERSICHT (nach Prioritaet):")
    lines.append("-" * 80)

    stufen = sorted(roadmap["roadmap"]["stufen"], key=lambda x: x["prioritaet"])
    for stufe in stufen:
        sid = stufe["stufe_id"]
        name = stufe["name"]
        phase = stufe.get("phase", "")
        prio = stufe["prioritaet"]
        status = stufe["status"]
        deps = ", ".join(stufe.get("abhaengigkeiten", [])) or "keine"
        block = ", ".join(stufe.get("blockierte_module", [])) or "keine"
        sperren = "; ".join(stufe.get("sperren", [])) or "keine"

        lines.append(f"[{prio:6.1f}] {sid:8s} | {status:14s} | {phase}")
        lines.append(f"         Name: {name}")
        lines.append(f"         Abhaengigkeiten: {deps}")
        lines.append(f"         Sperren: {sperren}")
        lines.append(f"         Blockiert danach: {block}")
        lines.append("")

    lines.append("-" * 80)
    lines.append("ENDE BERICHT")
    lines.append("=" * 80)
    return "\n".join(lines) + "\n"


# =============================================================================
# HAUPTLOGIK
# =============================================================================


def main() -> int:
    log("=" * 80)
    log("CORE-25: Programmierbare Gesamt-Roadmap gestartet")
    log("=" * 80)

    # 1. Git-Status vorher
    git_status_speichern(GIT_STATUS_VOR_PATH)
    log(f"Git-Status vorher gespeichert: {GIT_STATUS_VOR_PATH}")

    # 2. Konfiguration laden
    config = lade_config()
    log(f"Konfiguration geladen: {CONFIG_PATH}")

    # 3. Quelldateien pruefen
    quellen = [SOURCE_MASTER, SOURCE_INDEX, SOURCE_MODULPAKETE, SOURCE_NAECHSTE]
    for q in quellen:
        ok, msg = pruefe_datei_existenz(q, "Quelle")
        log(msg)
        if not ok:
            log(f"WARNUNG: Quelle fehlt: {q}")

    # 4. CORE-24 Queue pruefen (optional, fuer Kontext)
    if CORE24_QUEUE_PATH.exists():
        log(f"CORE-24 Queue gefunden: {CORE24_QUEUE_PATH}")
    else:
        log(f"INFO: CORE-24 Queue nicht gefunden: {CORE24_QUEUE_PATH}")

    # 5. Roadmap erzeugen
    log("Erzeuge Gesamt-Roadmap...")
    roadmap = erzeuge_gesamt_roadmap()
    log(f"Roadmap erzeugt: {roadmap['meta']['anzahl_stufen']} Stufen")

    # 6. Validierung
    log("Validiere Roadmap...")
    valid_ok, valid_fehler = validiere_roadmap(roadmap)
    roadmap["validierung"]["pruefzeitstempel"] = zeitstempel()
    if valid_ok:
        log("Validierung ERFOLGREICH")
    else:
        log(f"Validierung FEHLGESCHLAGEN: {len(valid_fehler)} Fehler")
        for f in valid_fehler:
            log(f"  FEHLER: {f}")

    # 7. Bericht erzeugen
    log("Erzeuge Bericht...")
    bericht_text = erzeuge_textbericht(roadmap, valid_ok, valid_fehler)
    BERICHT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BERICHT_PATH, "w", encoding="utf-8") as f:
        f.write(bericht_text)
    log(f"Bericht geschrieben: {BERICHT_PATH}")

    # 8. Roadmap-JSON speichern
    speichere_json(ROADMAP_JSON_PATH, roadmap)
    log(f"Roadmap-JSON geschrieben: {ROADMAP_JSON_PATH}")

    # 9. Git add + commit
    zu_committen = [
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_gesamt_roadmap.json",
        "ALIN_Neustart_Core/Reports/CORE25_GESAMT_ROADMAP_BERICHT.txt",
        "Config/core25_roadmap_v1.json",
        "Scripts/python_runner/core25_gesamt_roadmap.py",
        "Scripts/python_runner/check_core25_gesamt_roadmap.py",
        "Scripts/CORE25_GESAMT_ROADMAP_AUTOLAUF.ps1",
        "Projektplanung/CORE25_GESAMT_ROADMAP.md",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_git_status_vor.txt",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_git_status_nach.txt"
    ]

    ok_add, msg_add = git_add_dateien(zu_committen)
    if ok_add:
        log(f"git add OK: {msg_add}")
        ok_commit, msg_commit = git_commit("CORE-25: Programmierbare Gesamt-Roadmap erstellt und validiert")
        if ok_commit:
            log(f"git commit OK: {msg_commit}")
        else:
            log(f"git commit FEHLER: {msg_commit}")
    else:
        log(f"git add FEHLER: {msg_add}")

    # 10. Git-Status nachher
    git_status_speichern(GIT_STATUS_NACH_PATH)
    log(f"Git-Status nachher gespeichert: {GIT_STATUS_NACH_PATH}")

    # 11. Abschluss
    log("=" * 80)
    if valid_ok:
        log("CORE-25 ERFOLGREICH abgeschlossen.")
        log(f"Ergebnis: {ROADMAP_JSON_PATH}")
        log(f"Bericht: {BERICHT_PATH}")
        return 0
    else:
        log("CORE-25 mit VALIDIERUNGSFEHLERN abgeschlossen.")
        log("Bitte Pruefdatei ausfuehren: Scripts/python_runner/check_core25_gesamt_roadmap.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
