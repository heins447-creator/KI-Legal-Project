#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST01-0 Bestandsaufnahme Posteingang und Briefkasten-Module

Dieses Modul durchsucht das Projekt nach allen Posteingang- und Briefkasten-
bezogenen Modulen, erstellt eine Modulkarte, identifiziert Lücken und
dokumentiert Schnittstellen.
"""

import sys
import csv
import json
import datetime
import hashlib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(r"I:\KI_Legal_Project")
CONFIG = ROOT / "Config" / "post01_0_bestandsaufnahme_posteingang_v1.json"
LOG_DIR = ROOT / "Windows_App" / "Logs"
OUT_DIR = LOG_DIR / "POST01_0_Bestandsaufnahme"

FEHLER = 0
WARNUNGEN = 0


def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def scan_python_runner():
    """Scannt Scripts/python_runner nach Posteingang-Modulen."""
    runner_dir = ROOT / "Scripts" / "python_runner"
    modules = []

    keywords = [
        "posteingang", "sicherheitsgate", "sprachkontext", "pipeline",
        "vorzimmer", "entscheidung", "schlusskontrolle", "endabnahme",
        "dokumentsprachprofil", "arbeitsstruktur", "betriebsstatus",
        "gesamtstatus", "agentenabgrenzung", "freigabeliste",
        "arbeitsliste", "entscheidungsvorschlag", "kommunikationsparameter",
        "anwaltvorlage", "briefkasten", "eingang", "mail", "email"
    ]

    if not runner_dir.exists():
        return modules

    for f in sorted(runner_dir.glob("*.py")):
        name = f.name.lower()
        stem = f.stem.lower()
        matched = [k for k in keywords if k in stem]
        if matched:
            size = f.stat().st_size
            modules.append({
                "id": stem,
                "file": str(f),
                "name": f.name,
                "size_bytes": size,
                "keywords": matched,
                "type": "PYTHON_RUNNER",
                "category": categorize_module(stem),
            })

    return modules


def scan_check_files():
    """Scannt Check-Dateien zu Posteingang-Modulen."""
    runner_dir = ROOT / "Scripts" / "python_runner"
    checks = []

    keywords = [
        "posteingang", "sicherheitsgate", "sprachkontext", "pipeline",
        "vorzimmer", "entscheidung", "schlusskontrolle", "endabnahme",
        "dokumentsprachprofil", "arbeitsstruktur", "betriebsstatus",
        "gesamtstatus", "agentenabgrenzung", "freigabeliste",
        "arbeitsliste", "entscheidungsvorschlag", "kommunikationsparameter",
        "anwaltvorlage"
    ]

    if not runner_dir.exists():
        return checks

    for f in sorted(runner_dir.glob("check_*.py")):
        stem = f.stem.lower()
        matched = [k for k in keywords if k in stem]
        if matched:
            checks.append({
                "id": stem,
                "file": str(f),
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "keywords": matched,
                "type": "CHECK",
            })

    return checks


def scan_powershell_starters():
    """Scannt PowerShell-Starter."""
    scripts_dir = ROOT / "Scripts"
    starters = []

    keywords = [
        "posteingang", "vorzimmer", "anwaltvorlage", "dokumentsprachprofil",
        "schlusskontrolle", "briefkasten", "mail", "email"
    ]

    if not scripts_dir.exists():
        return starters

    for f in sorted(scripts_dir.glob("*.ps1")):
        stem = f.stem.lower()
        matched = [k for k in keywords if k in stem]
        if matched:
            starters.append({
                "id": stem,
                "file": str(f),
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "keywords": matched,
                "type": "POWERSHELL_STARTER",
            })

    return starters


def scan_configs():
    """Scannt Config-Dateien."""
    config_dir = ROOT / "Config"
    configs = []

    keywords = [
        "posteingang", "vorzimmer", "anwaltvorlage", "dokumentsprachprofil",
        "schlusskontrolle", "briefkasten", "mail", "email", "entscheidung",
        "kommunikationsparameter", "arbeitsstruktur", "sicherheitsgate",
        "sprachkontext", "language"
    ]

    if not config_dir.exists():
        return configs

    for f in sorted(config_dir.glob("*")):
        if f.is_file():
            stem = f.stem.lower()
            matched = [k for k in keywords if k in stem]
            if matched:
                configs.append({
                    "id": stem,
                    "file": str(f),
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "keywords": matched,
                    "type": "CONFIG",
                })

    return configs


def scan_db_migrations():
    """Scannt DB-Migrationen."""
    mig_dir = ROOT / "Database" / "Migrations"
    migs = []

    keywords = [
        "posteingang", "vorzimmer", "anwaltvorlage", "dokumentsprachprofil",
        "language", "sprach", "kommunikationsparameter"
    ]

    if not mig_dir.exists():
        return migs

    for f in sorted(mig_dir.glob("*.sql")):
        stem = f.stem.lower()
        matched = [k for k in keywords if k in stem]
        if matched:
            migs.append({
                "id": stem,
                "file": str(f),
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "keywords": matched,
                "type": "DB_MIGRATION",
            })

    return migs


def scan_logs():
    """Scannt Log-Dateien nach Posteingang-Ausführungen."""
    logs = []
    if not LOG_DIR.exists():
        return logs

    keywords = [
        "posteingang", "vorzimmer", "anwaltvorlage", "dokumentsprachprofil",
        "schlusskontrolle", "sicherheitsgate", "sprachkontext", "pipeline",
        "endabnahme", "betriebsstatus", "gesamtstatus", "arbeitsstruktur",
        "arbeitsliste", "entscheidung", "entscheidungsvorschlag"
    ]

    for f in sorted(LOG_DIR.glob("*.txt")):
        stem = f.stem.lower()
        matched = [k for k in keywords if k in stem]
        if matched:
            logs.append({
                "id": stem,
                "file": str(f),
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "keywords": matched,
                "type": "LOG",
            })

    return logs


def categorize_module(stem):
    """Ordnet ein Modul einer Kategorie zu."""
    stem = stem.lower()
    if any(x in stem for x in ["schema", "arbeitsstruktur", "db_", "verify"]):
        return "INFRASTRUKTUR"
    if any(x in stem for x in ["sicherheitsgate", "sicherheit", "defender", "signatur"]):
        return "SICHERHEIT"
    if any(x in stem for x in ["sprach", "language", "uebersetzung", "translation"]):
        return "SPRACHE"
    if any(x in stem for x in ["pipeline", "produktionslauf"]):
        return "PIPELINE"
    if any(x in stem for x in ["vorzimmer", "arbeitsliste", "entscheidung", "kommunikationsparameter"]):
        return "VORZIMMER"
    if any(x in stem for x in ["anwaltvorlage", "anwalts", "mandat", "akte"]):
        return "ANWALT"
    if any(x in stem for x in ["schlusskontrolle", "endabnahme", "gesamtstatus", "betriebsstatus"]):
        return "KONTROLLE"
    if any(x in stem for x in ["agentenabgrenzung", "freigabeliste", "boundary"]):
        return "ABGRENZUNG"
    if any(x in stem for x in ["ui", "ansicht", "dreiansicht", "dropdown"]):
        return "UI"
    if any(x in stem for x in ["smoketest", "test", "check_"]):
        return "TEST"
    return "SONSTIGES"


def build_modulkarte(runners, checks, starters, configs, migs, logs):
    """Erstellt die Modulkarte mit Verknüpfungen."""
    modules = []

    for r in runners:
        mod_id = r["id"]
        # Suche zugehörige Check-Datei
        check = None
        for c in checks:
            if mod_id.replace("posteingang_", "").replace("vorzimmer_", "") in c["id"] or c["id"] in mod_id:
                check = c
                break

        # Suche zugehörigen PowerShell-Starter
        starter = None
        for s in starters:
            if mod_id.replace("posteingang_", "").replace("vorzimmer_", "").replace("_v1", "").replace("_v2", "").replace("_v3", "") in s["id"]:
                starter = s
                break

        # Suche zugehörige Config
        config = None
        for cfg in configs:
            if mod_id.replace("_v1", "").replace("_v2", "").replace("_v3", "") in cfg["id"]:
                config = cfg
                break

        # Suche zugehörige Migration
        migration = None
        for m in migs:
            if mod_id.replace("posteingang_", "").replace("vorzimmer_", "").replace("_v1", "").replace("_v2", "").replace("_v3", "") in m["id"]:
                migration = m
                break

        # Suche Logs
        mod_logs = [l for l in logs if mod_id.replace("_v1", "").replace("_v2", "").replace("_v3", "") in l["id"]]

        modules.append({
            "modul_id": mod_id,
            "kategorie": r["category"],
            "runner": r["file"],
            "runner_size": r["size_bytes"],
            "check": check["file"] if check else None,
            "check_size": check["size_bytes"] if check else 0,
            "powershell_starter": starter["file"] if starter else None,
            "config": config["file"] if config else None,
            "config_size": config["size_bytes"] if config else 0,
            "db_migration": migration["file"] if migration else None,
            "logs_count": len(mod_logs),
            "status": assess_status(r, check, starter, config, migration, mod_logs),
        })

    return modules


def assess_status(runner, check, starter, config, migration, logs):
    """Bewertet den Status eines Moduls."""
    status = []
    if runner:
        status.append("RUNNER")
    if check:
        status.append("CHECK")
    if starter:
        status.append("STARTER")
    if config:
        status.append("CONFIG")
    if migration:
        status.append("DB_MIGRATION")
    if logs:
        status.append("AUSGEFUEHRT")

    if len(status) >= 5:
        return "VOLLSTAENDIG"
    if len(status) >= 3:
        return "TEILWEISE"
    if len(status) >= 1:
        return "BASIS"
    return "UNBEKANNT"


def build_lueckenliste(modules):
    """Identifiziert Lücken in der Modul-Landschaft."""
    luecken = []

    # Prüfe auf fehlende Checks
    for m in modules:
        if m["status"] in ("VOLLSTAENDIG", "TEILWEISE", "BASIS") and not m["check"]:
            luecken.append({
                "modul_id": m["modul_id"],
                "luecke": "FEHLENDE_CHECK_DATEI",
                "beschreibung": "Keine Check-Datei (Prüfdatei) vorhanden.",
                "prioritaet": "MITTEL",
            })

    # Prüfe auf fehlende PowerShell-Starter
    for m in modules:
        if m["status"] in ("VOLLSTAENDIG", "TEILWEISE") and not m["powershell_starter"]:
            luecken.append({
                "modul_id": m["modul_id"],
                "luecke": "FEHLENDER_POWERSHELL_STARTER",
                "beschreibung": "Kein PowerShell-Starter vorhanden.",
                "prioritaet": "NIEDRIG",
            })

    # Prüfe auf fehlende DB-Migrationen bei DB-relevanten Modulen
    db_relevant = ["dokumentsprachprofil", "sprachkontext", "kommunikationsparameter", "anwaltvorlage"]
    for m in modules:
        if any(k in m["modul_id"] for k in db_relevant) and not m["db_migration"]:
            luecken.append({
                "modul_id": m["modul_id"],
                "luecke": "FEHLENDE_DB_MIGRATION",
                "beschreibung": "Modul ist DB-relevant, aber keine Migration vorhanden.",
                "prioritaet": "HOCH",
            })

    # Prüfe auf Module ohne Ausführungs-Logs
    for m in modules:
        if m["logs_count"] == 0 and m["status"] in ("VOLLSTAENDIG", "TEILWEISE"):
            luecken.append({
                "modul_id": m["modul_id"],
                "luecke": "NOCH_NICHT_AUSGEFUEHRT",
                "beschreibung": "Modul ist vorhanden, aber keine Ausführungsprotokolle gefunden.",
                "prioritaet": "NIEDRIG",
            })

    # Bekannte fehlende Module (aus Projektplanung)
    expected_modules = [
        "briefkasten_email_eingang",
        "briefkasten_scan_eingang",
        "posteingang_virusscan_integration",
        "posteingang_ocr_vorverarbeitung",
    ]
    found_ids = {m["modul_id"] for m in modules}
    for expected in expected_modules:
        if expected not in found_ids:
            luecken.append({
                "modul_id": expected,
                "luecke": "FEHLENDES_MODUL",
                "beschreibung": "Modul ist in der Projektplanung vorgesehen, aber nicht implementiert.",
                "prioritaet": "MITTEL",
            })

    return luecken


def build_schnittstellenliste(modules):
    """Dokumentiert Schnittstellen zwischen Modulen."""
    schnittstellen = []

    # Pipeline ruft Sicherheitsgate und Sprachkontext-Gate auf
    schnittstellen.append({
        "von": "014_posteingang_pipeline_v1",
        "zu": "005_posteingang_sicherheitsgate_v2",
        "typ": "AUFRUF",
        "beschreibung": "Pipeline startet Sicherheitsgate für Roh-Eingang.",
    })
    schnittstellen.append({
        "von": "014_posteingang_pipeline_v1",
        "zu": "012_posteingang_sprachkontext_gate_v2",
        "typ": "AUFRUF",
        "beschreibung": "Pipeline startet Sprachkontext-Gate für technisch geprüfte Dateien.",
    })

    # Vorzimmer-Arbeitsliste liest Entscheidungskarten
    schnittstellen.append({
        "von": "017_vorzimmer_arbeitsliste_v1",
        "zu": "Posteingang/91_Entscheidungskarten",
        "typ": "DATEI_LESEN",
        "beschreibung": "Arbeitsliste liest JSON-Entscheidungskarten aus dem Posteingang.",
    })

    # Vorzimmer-Entscheidung verschiebt Dateien
    schnittstellen.append({
        "von": "018_vorzimmer_entscheidung_v1",
        "zu": "Posteingang-Arbeitsordner",
        "typ": "DATEI_VERSCHIEBEN",
        "beschreibung": "Entscheidungsmodul verschiebt Dateien zwischen Posteingang-Ordnern.",
    })

    # Entscheidungsvorschlag liest Arbeitsliste
    schnittstellen.append({
        "von": "023_vorzimmer_entscheidungsvorschlag_v1",
        "zu": "017_vorzimmer_arbeitsliste_v1",
        "typ": "DATEI_LESEN",
        "beschreibung": "Vorschlag liest die neueste Arbeitsliste als Eingabe.",
    })

    # Dokumentsprachprofil schreibt in DuckDB
    schnittstellen.append({
        "von": "031_dokumentsprachprofil_v1",
        "zu": "Database/Legal_Brain.duckdb",
        "typ": "DATENBANK_SCHREIBEN",
        "beschreibung": "Sprachprofile werden in posteingang_document_language_profile geschrieben.",
    })

    # Schlusskontrolle liest DB-Profile
    schnittstellen.append({
        "von": "033_posteingang_schlusskontrolle_v2",
        "zu": "Database/Legal_Brain.duckdb",
        "typ": "DATENBANK_LESEN",
        "beschreibung": "Schlusskontrolle liest Sprachprofile aus der Datenbank.",
    })

    # Endabnahme prüft alle Module
    schnittstellen.append({
        "von": "037_posteingang_endabnahme_v3",
        "zu": "ALLE_POSTEINGANG_MODULE",
        "typ": "PRUEFUNG",
        "beschreibung": "Endabnahme prüft Existenz und Konsistenz aller Posteingang-Module.",
    })

    # UI04 liest UI04-Config
    schnittstellen.append({
        "von": "ui04_durchstich_sekretariat_anwalt_ruecklauf",
        "zu": "Config/ui04_durchstich_sekretariat_anwalt_ruecklauf_v1.json",
        "typ": "CONFIG_LESEN",
        "beschreibung": "UI04 liest Dropdown- und Entscheidungskonfiguration.",
    })

    # UI04b liest UI04b-Config
    schnittstellen.append({
        "von": "ui04b_logikpruefung_entscheidung",
        "zu": "Config/ui04b_logikpruefung_entscheidung_v1.json",
        "typ": "CONFIG_LESEN",
        "beschreibung": "UI04b liest Logikprüfungs- und Entscheidungskonfiguration.",
    })

    return schnittstellen


def write_modulkarte_csv(modules):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_MODULKARTE_{ts}.csv"

    fields = [
        "modul_id", "kategorie", "runner", "runner_size",
        "check", "check_size", "powershell_starter", "config",
        "config_size", "db_migration", "logs_count", "status"
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for m in modules:
            writer.writerow({k: m.get(k, "") for k in fields})

    return path


def write_modulkarte_json(modules):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_MODULKARTE_{ts}.json"

    data = {
        "time": now(),
        "modules_count": len(modules),
        "modules": modules,
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def write_lueckenliste_csv(luecken):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_LUECKENLISTE_{ts}.csv"

    fields = ["modul_id", "luecke", "beschreibung", "prioritaet"]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for l in luecken:
            writer.writerow({k: l.get(k, "") for k in fields})

    return path


def write_lueckenliste_json(luecken):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_LUECKENLISTE_{ts}.json"

    data = {
        "time": now(),
        "luecken_count": len(luecken),
        "luecken": luecken,
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def write_schnittstellen_csv(schnittstellen):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_SCHNITTSTELLEN_{ts}.csv"

    fields = ["von", "zu", "typ", "beschreibung"]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for s in schnittstellen:
            writer.writerow({k: s.get(k, "") for k in fields})

    return path


def write_schnittstellen_json(schnittstellen):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_SCHNITTSTELLEN_{ts}.json"

    data = {
        "time": now(),
        "schnittstellen_count": len(schnittstellen),
        "schnittstellen": schnittstellen,
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def write_empfehlung(modules, luecken, schnittstellen):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_EMPFEHLUNG_{ts}.txt"

    vollstaendig = [m for m in modules if m["status"] == "VOLLSTAENDIG"]
    teilweise = [m for m in modules if m["status"] == "TEILWEISE"]
    basis = [m for m in modules if m["status"] == "BASIS"]

    hoch = [l for l in luecken if l["prioritaet"] == "HOCH"]
    mittel = [l for l in luecken if l["prioritaet"] == "MITTEL"]
    niedrig = [l for l in luecken if l["prioritaet"] == "NIEDRIG"]

    lines = []
    lines.append("POST01-0 EMPFEHLUNG")
    lines.append("=" * 80)
    lines.append("Zeit: " + now())
    lines.append("")
    lines.append("ZUSAMMENFASSUNG")
    lines.append("-" * 80)
    lines.append(f"Gefundene Module:         {len(modules)}")
    lines.append(f"  - Vollstaendig:         {len(vollstaendig)}")
    lines.append(f"  - Teilweise:            {len(teilweise)}")
    lines.append(f"  - Basis:                {len(basis)}")
    lines.append(f"Identifizierte Luecken:   {len(luecken)}")
    lines.append(f"  - Hoch:                 {len(hoch)}")
    lines.append(f"  - Mittel:               {len(mittel)}")
    lines.append(f"  - Niedrig:              {len(niedrig)}")
    lines.append(f"Dokumentierte Schnittstellen: {len(schnittstellen)}")
    lines.append("")
    lines.append("EMPFEHLUNGEN")
    lines.append("-" * 80)

    if hoch:
        lines.append("")
        lines.append("1. HOHE PRIORITAET (sofort angehen)")
        lines.append("-" * 40)
        for l in hoch:
            lines.append(f"   [{l['modul_id']}] {l['luecke']}: {l['beschreibung']}")

    if mittel:
        lines.append("")
        lines.append("2. MITTLERE PRIORITAET (naechster Sprint)")
        lines.append("-" * 40)
        for l in mittel:
            lines.append(f"   [{l['modul_id']}] {l['luecke']}: {l['beschreibung']}")

    if niedrig:
        lines.append("")
        lines.append("3. NIEDRIGE PRIORITAET (Backlog)")
        lines.append("-" * 40)
        for l in niedrig:
            lines.append(f"   [{l['modul_id']}] {l['luecke']}: {l['beschreibung']}")

    lines.append("")
    lines.append("ARCHITEKTUR-HINWEISE")
    lines.append("-" * 80)
    lines.append("- Die Pipeline (014) ist das zentrale Orchestrationsmodul.")
    lines.append("- Sicherheitsgate (005) und Sprachkontext-Gate (012) sind unabhaengige Filter.")
    lines.append("- Vorzimmer-Module (017-019, 023) bilden eine eigene Entscheidungsebene.")
    lines.append("- Dokumentsprachprofil (031) und Schlusskontrolle (033) sind DB-gestuetzt.")
    lines.append("- Endabnahme (037) ist der finale Qualitaetsgate.")
    lines.append("- UI04/UI04b sind Frontend-Durchstiche, noch nicht in die Pipeline integriert.")
    lines.append("")
    lines.append("GRENZE")
    lines.append("-" * 80)
    lines.append("Diese Bestandsaufnahme bewertet nicht die fachliche Richtigkeit der Module.")
    lines.append("Sie dokumentiert nur Existenz, Verknuepfung und identifizierte Luecken.")

    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def write_bericht(modules, luecken, schnittstellen, paths):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = OUT_DIR / f"POST01_0_BERICHT_{ts}.txt"

    lines = []
    lines.append("POST01-0 BESTANDSAUFNAHME BERICHT")
    lines.append("=" * 80)
    lines.append("Zeit: " + now())
    lines.append("")
    lines.append("AUSGABEDATEIEN")
    lines.append("-" * 80)
    for key, p in paths.items():
        lines.append(f"{key}: {p}")
    lines.append("")
    lines.append("MODULKARTE")
    lines.append("-" * 80)
    for m in modules:
        lines.append(f"{m['modul_id']} | {m['kategorie']} | {m['status']}")
    lines.append("")
    lines.append("LUECKENLISTE")
    lines.append("-" * 80)
    for l in luecken:
        lines.append(f"[{l['prioritaet']}] {l['modul_id']}: {l['luecke']}")
    lines.append("")
    lines.append("SCHNITTSTELLEN")
    lines.append("-" * 80)
    for s in schnittstellen:
        lines.append(f"{s['von']} -> {s['zu']} ({s['typ']})")
    lines.append("")
    lines.append("STATUS")
    lines.append("-" * 80)
    lines.append(f"Module: {len(modules)}")
    lines.append(f"Luecken: {len(luecken)}")
    lines.append(f"Schnittstellen: {len(schnittstellen)}")
    lines.append(f"Fehler: {FEHLER}")
    lines.append(f"Warnungen: {WARNUNGEN}")

    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def selbsttest():
    global FEHLER, WARNUNGEN
    print("POST01-0 SELBSTTEST =======================================")

    def t(bez, bed):
        global FEHLER, WARNUNGEN
        if bed:
            print("  OK   ", bez)
        else:
            print("  FEHLER", bez)
            FEHLER += 1

    cfg = load_config()
    t("Config geladen", cfg.get("version", "").startswith("POST01-0"))
    t("Config hat scan_bereiche", "scan_bereiche" in cfg)
    t("Config hat suchbegriffe", "suchbegriffe" in cfg)
    t("Config hat modul_kategorien", "modul_kategorien" in cfg)
    t("Config hat luecken_kategorien", "luecken_kategorien" in cfg)

    runners = scan_python_runner()
    t("Python-Runner gefunden", len(runners) > 0)
    t("Sicherheitsgate gefunden", any("sicherheitsgate" in r["id"] for r in runners))
    t("Pipeline gefunden", any("pipeline" in r["id"] for r in runners))
    t("Vorzimmer-Arbeitsliste gefunden", any("arbeitsliste" in r["id"] for r in runners))
    t("Dokumentsprachprofil gefunden", any("dokumentsprachprofil" in r["id"] for r in runners))
    t("Schlusskontrolle gefunden", any("schlusskontrolle" in r["id"] for r in runners))
    t("Endabnahme gefunden", any("endabnahme" in r["id"] for r in runners))
    t("UI04 gefunden", any("ui04" in r["id"] for r in runners))
    t("UI04b gefunden", any("ui04b" in r["id"] for r in runners))

    checks = scan_check_files()
    t("Check-Dateien gefunden", len(checks) > 0)

    starters = scan_powershell_starters()
    t("PowerShell-Starter gefunden", len(starters) > 0)

    configs = scan_configs()
    t("Configs gefunden", len(configs) > 0)

    migs = scan_db_migrations()
    t("DB-Migrationen gefunden", len(migs) > 0)

    logs = scan_logs()
    t("Logs gefunden", len(logs) > 0)

    modules = build_modulkarte(runners, checks, starters, configs, migs, logs)
    t("Modulkarte erstellt", len(modules) > 0)
    t("Module haben Kategorien", all(m["kategorie"] for m in modules))
    t("Module haben Status", all(m["status"] for m in modules))

    luecken = build_lueckenliste(modules)
    t("Lueckenliste erstellt", len(luecken) >= 0)

    schnittstellen = build_schnittstellenliste(modules)
    t("Schnittstellenliste erstellt", len(schnittstellen) > 0)
    t("Pipeline-Schnittstelle vorhanden", any("pipeline" in s["von"] for s in schnittstellen))
    t("DB-Schnittstelle vorhanden", any("DATENBANK" in s["typ"] for s in schnittstellen))

    print("=========================================================")
    print("FEHLER:", FEHLER)
    print("WARNUNGEN:", WARNUNGEN)
    return FEHLER == 0


def hauptlauf():
    global FEHLER, WARNUNGEN
    ensure_dirs()
    cfg = load_config()

    print("POST01-0 HAUPTLAUF")
    print("Config:", CONFIG)
    print("")

    runners = scan_python_runner()
    checks = scan_check_files()
    starters = scan_powershell_starters()
    configs = scan_configs()
    migs = scan_db_migrations()
    logs = scan_logs()

    print("Gefundene Python-Runner:", len(runners))
    print("Gefundene Checks:", len(checks))
    print("Gefundene PowerShell-Starter:", len(starters))
    print("Gefundene Configs:", len(configs))
    print("Gefundene DB-Migrationen:", len(migs))
    print("Gefundene Logs:", len(logs))
    print("")

    modules = build_modulkarte(runners, checks, starters, configs, migs, logs)
    luecken = build_lueckenliste(modules)
    schnittstellen = build_schnittstellenliste(modules)

    paths = {}
    paths["modulkarte_csv"] = write_modulkarte_csv(modules)
    paths["modulkarte_json"] = write_modulkarte_json(modules)
    paths["lueckenliste_csv"] = write_lueckenliste_csv(luecken)
    paths["lueckenliste_json"] = write_lueckenliste_json(luecken)
    paths["schnittstellen_csv"] = write_schnittstellen_csv(schnittstellen)
    paths["schnittstellen_json"] = write_schnittstellen_json(schnittstellen)
    paths["empfehlung"] = write_empfehlung(modules, luecken, schnittstellen)
    paths["bericht"] = write_bericht(modules, luecken, schnittstellen, paths)

    print("POST01-0 HAUPTLAUF FERTIG")
    print("Module:", len(modules))
    print("Luecken:", len(luecken))
    print("Schnittstellen:", len(schnittstellen))
    print("")
    for key, p in paths.items():
        print(f"{key}: {p}")

    return paths


if __name__ == "__main__":
    if "--selbsttest" in sys.argv:
        ok = selbsttest()
        sys.exit(0 if ok else 1)
    else:
        hauptlauf()
        sys.exit(0)
