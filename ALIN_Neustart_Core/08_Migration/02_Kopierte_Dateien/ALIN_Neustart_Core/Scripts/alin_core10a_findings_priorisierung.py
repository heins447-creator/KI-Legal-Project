#!/usr/bin/env python3
"""
CORE-10a – Findings priorisieren und Reparaturauftraege ableiten
================================================================
Auftrag:  Lesen der CORE-10 Berichte, P0-P3-Priorisierung erstellen,
          Reparaturplan dokumentieren. KEINE Registeraenderungen.
Harte Grenzen (AGENTS.md):
  - Keine Aenderungen ausserhalb von I:\KI_Legal_Project
  - Keine echten Mandantendaten an externe Modelle
  - Keine API-Schluessel in Git
  - Keine endgueltige Rechtsberatung
  - Keine Beweiswuerdigung
  - Keine Tuerschwelle, bevor Quellenregister, Fachanwaltsraster,
    Quellenbetreuer, Adapter, Cache und Offline-Fallback stehen.
Lieferpflicht:
  - Python-Laeufer unter Scripts\python_runner
  - Pruefdatei unter Scripts\python_runner
  - PowerShell-Starter unter Scripts
  - Dokumentation unter Projektplanung
  - Bericht unter Windows_App\Logs
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# ============================================================================
# KONFIGURATION
# ============================================================================
BASE_DIR = Path("ALIN_Neustart_Core")
REPORTS_DIR = BASE_DIR / "Reports"
REGISTER_DIR = BASE_DIR / "01_Register"
SCHNITTSTELLEN_DIR = BASE_DIR / "03_Schnittstellen"
LOG_DIR = Path("Windows_App") / "Logs"

# P0-P3 Priorisierungsregeln
PRIORITAET = {
    "P0": "KRITISCH – Sofortreparatur erforderlich. Systemkonsistenz gefaehrdet.",
    "P1": "HOCH – Naechster Sprint. Funktionale Luecken, keine sofortige Gefaehrdung.",
    "P2": "MITTEL – Geplant. Qualitaetsmaengel, Workarounds moeglich.",
    "P3": "NIEDRIG – Dokumentieren. Informationell, kein Reparaturbedarf.",
}

# Mapping: Pruefungsnummer -> Prioritaet
PRUEFUNG_ZU_PRIO = {
    "P02": "P0",   # Fehlende Abhaengigkeiten
    "P03": "P0",   # Widerspruechliche Modulnamen (SQL-Code)
    "P10": "P0",   # Querregister-Verknuepfungen (fehlende Ressourcen)
    "P09": "P1",   # Schema-Luecken
    "P04": "P2",   # Platzhalter-Eingaben/Ausgaben
    "P08": "P2",   # Unklare Schnittstellen (identisch mit P04)
    "P06": "P3",   # DB-aendernde Module (informationell)
    "P07": "P3",   # Online-faehige Module (informationell)
}

# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def log(msg):
    print(msg)

def lade_json(pfad):
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)

def lade_bericht(pfad):
    """Liest den CORE-10 Detail-Pruefbericht zeilenweise."""
    if not pfad.exists():
        return []
    with open(pfad, "r", encoding="utf-8") as f:
        return f.readlines()

# ============================================================================
# PARSER FUER CORE-10 BERICHT
# ============================================================================

def parse_core10_bericht(zeilen):
    """
    Parst den CORE-10 Detailbericht und gruppiert nach Pruefungen.
    Rueckgabe: dict {pruef_id: [findings]}
    """
    ergebnis = defaultdict(list)
    aktuelle_pruefung = None
    
    for zeile in zeilen:
        zeile = zeile.strip()
        if not zeile or zeile.startswith("==") or zeile.startswith("--"):
            continue
        if zeile.startswith("ENDE"):
            break
        
        # Pruefungsheader erkennen
        if zeile.startswith("Pruefung "):
            # Format: "Pruefung 01: Modul-ID-Eindeutigkeit"
            teile = zeile.split(":", 1)
            if teile:
                nummer = teile[0].replace("Pruefung ", "").strip()
                aktuelle_pruefung = f"P{nummer.zfill(2)}"
            continue
        
        if zeile == "OK – keine Auffaelligkeiten.":
            continue
        
        if aktuelle_pruefung and zeile:
            ergebnis[aktuelle_pruefung].append(zeile)
    
    return dict(ergebnis)

# ============================================================================
# ANALYSE FUNKTIONEN
# ============================================================================

def analyse_p02_fehlende_abhaengigkeiten(findings):
    """P02: Fehlende Abhaengigkeiten -> P0"""
    betroffene = []
    for f in findings:
        if "FEHLENDE_ABHAENGIGKEIT" in f:
            # Format: FEHLENDE_ABHAENGIGKEIT modul='X' referenziert unbekanntes Modul 'Y'
            betroffene.append(f)
    return {
        "anzahl": len(betroffene),
        "details": betroffene,
        "problem": "Modul referenziert nicht-existentes Abhaengigkeitsmodul. Laufzeitfehler wahrscheinlich.",
        "risiko": "HOCH – Modul kann nicht ausgefuehrt werden, da Abhaengigkeit fehlt.",
        "erlaubte_aenderungen": "Modulregister.json: abhaengigkeiten korrigieren oder fehlendes Modul nachinventarisieren.",
        "verbotene_aenderungen": "Keine Aenderung an Quellcode der referenzierten (nicht existenten) Module.",
        "folgeauftrag": "CORE-10a-P02: Abhaengigkeit korrigieren – entweder ui01_anwaltsansicht nachinventarisieren oder Referenz entfernen.",
        "anwalt_pruefung": False,
    }

def analyse_p03_widerspruechliche_namen(findings):
    """P03: Widerspruechliche Modulnamen -> P0"""
    module_betroffen = set()
    sql_namen = set()
    for f in findings:
        if "WIDERSPRUCH" in f:
            # Extrahiere modulname
            if "modulname='" in f:
                start = f.find("modulname='") + 11
                end = f.find("'", start)
                name = f[start:end]
                sql_namen.add(name)
            # Extrahiere IDs
            if "id1='" in f:
                start = f.find("id1='") + 5
                end = f.find("'", start)
                module_betroffen.add(f[start:end])
            if "id2='" in f:
                start = f.find("id2='") + 5
                end = f.find("'", start)
                module_betroffen.add(f[start:end])
    
    return {
        "anzahl": len(findings),
        "anzahl_module": len(module_betroffen),
        "sql_namen": sorted(sql_namen),
        "details": findings[:5] + ["... (weitere ausgelassen)"] if len(findings) > 5 else findings,
        "problem": "20 Module haben SQL-Code als modulname (z.B. 'SELECT table_name', 'SELECT COUNT(*)'). CORE-09-Heuristik hat SQL-Fragmente statt Dateinamen extrahiert.",
        "risiko": "HOCH – Registerabfragen nach Modulnamen liefern falsche Ergebnisse. Konsistenzpruefungen werden unbrauchbar.",
        "erlaubte_aenderungen": "Modulregister.json: modulname korrigieren auf Basis des Dateinamens (ohne Pfad/Endung).",
        "verbotene_aenderungen": "Keine Aenderung an den Python-Quelldateien selbst (nur Register-Metadaten).",
        "folgeauftrag": "CORE-10a-P03: Heuristik in CORE-09 korrigieren (determine_modulname) und 20 Modulnamen im Register bereinigen.",
        "anwalt_pruefung": False,
    }

def analyse_p10_querregister(findings):
    """P10: Querregister-Verknuepfungen -> P0"""
    ressourcen_fehlend = defaultdict(list)
    for f in findings:
        if "UNGUELTIGE_RESSOURCE" in f:
            # Format: UNGUELTIGE_RESSOURCE modul='X' ressource='Y'
            mod_start = f.find("modul='") + 7
            mod_end = f.find("'", mod_start)
            modul = f[mod_start:mod_end]
            res_start = f.find("ressource='") + 11
            res_end = f.find("'", res_start)
            ressource = f[res_start:res_end]
            ressourcen_fehlend[ressource].append(modul)
    
    eindeutige_ressourcen = sorted(ressourcen_fehlend.keys())
    eindeutige_module = set()
    for mods in ressourcen_fehlend.values():
        eindeutige_module.update(mods)
    
    return {
        "anzahl": len(findings),
        "anzahl_ressourcen": len(eindeutige_ressourcen),
        "anzahl_module": len(eindeutige_module),
        "fehlende_ressourcen": eindeutige_ressourcen,
        "details": [f"{res}: {len(mods)} Module" for res, mods in sorted(ressourcen_fehlend.items())],
        "problem": "186 Verweise auf Ressourcen, die im ressourcenregister.json nicht existieren. TESS_SPA, TESS_NLD, TESS_POL (Tesseract-Sprachpakete) und ARGOS_DE_* (Argos-Translate-Sprachpaare) fehlen.",
        "risiko": "MITTEL-HOCH – Module koennen nicht ausgefuehrt werden, wenn Ressourcen fehlen. Offline-Betrieb auf Gerichtslaptop beeintraechtigt.",
        "erlaubte_aenderungen": "Ressourcenregister.json: Fehlende Ressourcen nachinventarisieren ODER Modulregister: Verweise entfernen, wenn Ressourcen nicht mehr benoetigt.",
        "verbotene_aenderungen": "Keine Installation tatsaechlicher Tesseract/Argos-Pakete (nur Register-Eintragung).",
        "folgeauftrag": "CORE-10a-P10: Ressourcenregister vervollstaendigen (TESS_* und ARGOS_DE_*) oder Modulregister bereinigen.",
        "anwalt_pruefung": False,
    }

def analyse_p09_schema_luecken(findings):
    """P09: Schema-Luecken -> P1"""
    module_betroffen = []
    for f in findings:
        if "SCHEMA_LUECKE" in f:
            mod_start = f.find("modul='") + 7
            mod_end = f.find("'", mod_start)
            module_betroffen.append(f[mod_start:mod_end])
    
    return {
        "anzahl": len(findings),
        "anzahl_module": len(module_betroffen),
        "module": sorted(module_betroffen),
        "details": findings,
        "problem": "16 Module liefern Daten an andere Module, aber ihr Bereich passt zu keinem der 8 definierten Schnittstellen-Schemas. Neue Uebergaben (vorzimmer, agent, quellen, sprache, ui) sind nicht abgedeckt.",
        "risiko": "MITTEL – Keine Schema-Validierung moeglich. Datenformat-Inkonsistenzen zwischen Modulen wahrscheinlich.",
        "erlaubte_aenderungen": "Neue Schnittstellen-Schemas erstellen (03_Schnittstellen/) oder Bereichszuordnung korrigieren.",
        "verbotene_aenderungen": "Keine Aenderung an Modul-Quellcode ohne begleitende Schema-Aenderung.",
        "folgeauftrag": "CORE-10a-P09: Schnittstellen-Schemas fuer Bereiche 'vorzimmer', 'agent', 'quellen', 'sprache', 'ui' erstellen.",
        "anwalt_pruefung": False,
    }

def analyse_p04_p08_platzhalter(findings_p04, findings_p08):
    """P04/P08: Platzhalter-Eingaben/Ausgaben -> P2"""
    module_p04 = set()
    for f in findings_p04:
        if "LEER_EINGABE" in f or "LEER_AUSGABE" in f:
            mod_start = f.find("modul='") + 7
            mod_end = f.find("'", mod_start)
            module_p04.add(f[mod_start:mod_end])
    
    return {
        "anzahl": len(findings_p04) + len(findings_p08),
        "anzahl_module": len(module_p04),
        "module": sorted(module_p04),
        "details": [],
        "problem": "48 PowerShell-Starter haben identische Platzhalter-Beschreibungen fuer Eingabe/Ausgabe ('Konfiguration und Umgebungsvariablen' / 'Prozess-Start, Log-Datei, Exit-Code'). Keine spezifische Schnittstellenbeschreibung.",
        "risiko": "NIEDRIG-MITTEL – Eingabe/Ausgabe nicht dokumentiert. Wartung und Fehlersuche erschwert.",
        "erlaubte_aenderungen": "Modulregister.json: eingabe/ausgabe auf spezifische Parameter erweitern.",
        "verbotene_aenderungen": "Keine Aenderung an PowerShell-Skripten selbst (nur Register-Metadaten).",
        "folgeauftrag": "CORE-10a-P04: PowerShell-Starter-Eingaben/Ausgaben im Register verfeinern.",
        "anwalt_pruefung": False,
    }

def analyse_p06_db_aendernd(findings):
    """P06: DB-aendernde Module -> P3"""
    module = []
    for f in findings:
        if "DB_AENDERUNG" in f:
            mod_start = f.find("modul='") + 7
            mod_end = f.find("'", mod_start)
            module.append(f[mod_start:mod_end])
    
    return {
        "anzahl": len(findings),
        "module": sorted(module),
        "details": findings,
        "problem": "18 Module haben darf_datenbank_aendern=true. Darunter 7 python_runner und 11 datenbank_migration.",
        "risiko": "NIEDRIG – Informationell. Kein Fehler, aber wichtig fuer Backup/Restore-Planung.",
        "erlaubte_aenderungen": "Keine (nur Dokumentation).",
        "verbotene_aenderungen": "Keine Aenderung der Berechtigungen ohne Architektur-Review.",
        "folgeauftrag": "Dokumentation aktualisieren: Liste DB-aendernder Module in Backup-Konzept uebernehmen.",
        "anwalt_pruefung": False,
    }

def analyse_p07_online_faehig(findings):
    """P07: Online-faehige Module -> P3"""
    module = []
    for f in findings:
        if "ONLINE_FAEHIG" in f:
            mod_start = f.find("modul='") + 7
            mod_end = f.find("'", mod_start)
            module.append(f[mod_start:mod_end])
    
    return {
        "anzahl": len(findings),
        "module": sorted(module),
        "details": findings,
        "problem": "13 Module haben darf_online_gehen=true. Darunter 5 PowerShell-Starter und 8 Python-Module.",
        "risiko": "NIEDRIG – Informationell. Wichtig fuer Offline-Gerichtslaptop-Konfiguration.",
        "erlaubte_aenderungen": "Keine (nur Dokumentation).",
        "verbotene_aenderungen": "Keine Aenderung der Online-Berechtigungen ohne Datenschutz-Review.",
        "folgeauftrag": "Dokumentation aktualisieren: Liste online-faehiger Module in Offline-Konzept uebernehmen.",
        "anwalt_pruefung": False,
    }

# ============================================================================
# HAUPTANALYSE
# ============================================================================

def main():
    log("=" * 70)
    log("CORE-10a – Findings priorisieren und Reparaturauftraege ableiten")
    log("=" * 70)
    
    # Bericht laden
    bericht_pfad = REPORTS_DIR / "ALIN_CORE10_PRUEFBERICHT.txt"
    if not bericht_pfad.exists():
        log(f"FEHLER: Bericht nicht gefunden: {bericht_pfad}")
        sys.exit(1)
    
    zeilen = lade_bericht(bericht_pfad)
    gruppiert = parse_core10_bericht(zeilen)
    
    log(f"\nGeladene Pruefungen: {list(gruppiert.keys())}")
    log(f"Gesamtfindings: {sum(len(v) for v in gruppiert.values())}")
    
    # Analysen durchfuehren
    analysen = {}
    
    if "P02" in gruppiert:
        analysen["P02"] = analyse_p02_fehlende_abhaengigkeiten(gruppiert["P02"])
    if "P03" in gruppiert:
        analysen["P03"] = analyse_p03_widerspruechliche_namen(gruppiert["P03"])
    if "P10" in gruppiert:
        analysen["P10"] = analyse_p10_querregister(gruppiert["P10"])
    if "P09" in gruppiert:
        analysen["P09"] = analyse_p09_schema_luecken(gruppiert["P09"])
    
    p04 = gruppiert.get("P04", [])
    p08 = gruppiert.get("P08", [])
    if p04 or p08:
        analysen["P04_P08"] = analyse_p04_p08_platzhalter(p04, p08)
    
    if "P06" in gruppiert:
        analysen["P06"] = analyse_p06_db_aendernd(gruppiert["P06"])
    if "P07" in gruppiert:
        analysen["P07"] = analyse_p07_online_faehig(gruppiert["P07"])
    
    # Priorisierung aufbauen
    priorisierung = {"P0": [], "P1": [], "P2": [], "P3": []}
    for pruef_id, analyse in analysen.items():
        prio = PRUEFUNG_ZU_PRIO.get(pruef_id, "P3")
        priorisierung[prio].append({
            "pruefung": pruef_id,
            "anzahl": analyse["anzahl"],
            "problem": analyse["problem"],
            "risiko": analyse["risiko"],
            "folgeauftrag": analyse["folgeauftrag"],
            "anwalt_pruefung": analyse["anwalt_pruefung"],
        })
    
    # Bericht schreiben
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bericht = []
    bericht.append("=" * 70)
    bericht.append("CORE-10a FINDINGS-PRIORISIERUNG UND REPARATURPLAN")
    bericht.append(f"Erstellt: {timestamp}")
    bericht.append("=" * 70)
    bericht.append("")
    bericht.append("ZUSAMMENFASSUNG")
    bericht.append("-" * 70)
    bericht.append(f"Gesamtfindings aus CORE-10: {sum(len(v) for v in gruppiert.values())}")
    bericht.append(f"P0 (Kritisch):     {sum(a['anzahl'] for a in priorisierung['P0'])} Findings")
    bericht.append(f"P1 (Hoch):         {sum(a['anzahl'] for a in priorisierung['P1'])} Findings")
    bericht.append(f"P2 (Mittel):       {sum(a['anzahl'] for a in priorisierung['P2'])} Findings")
    bericht.append(f"P3 (Niedrig):      {sum(a['anzahl'] for a in priorisierung['P3'])} Findings")
    bericht.append("")
    
    for prio in ["P0", "P1", "P2", "P3"]:
        bericht.append("=" * 70)
        bericht.append(f"{prio}: {PRIORITAET[prio]}")
        bericht.append("=" * 70)
        bericht.append("")
        
        for item in priorisierung[prio]:
            bericht.append(f"  Pruefung: {item['pruefung']}")
            bericht.append(f"  Anzahl:   {item['anzahl']} Findings")
            bericht.append(f"  Problem:  {item['problem']}")
            bericht.append(f"  Risiko:   {item['risiko']}")
            bericht.append(f"  Folge:    {item['folgeauftrag']}")
            bericht.append(f"  Anwalt:   {'Ja' if item['anwalt_pruefung'] else 'Nein'}")
            bericht.append("")
    
    # Detailanalysen anhaengen
    bericht.append("=" * 70)
    bericht.append("DETAILANALYSEN")
    bericht.append("=" * 70)
    bericht.append("")
    
    for pruef_id, analyse in analysen.items():
        bericht.append(f"--- {pruef_id} ---")
        bericht.append(f"Anzahl: {analyse['anzahl']}")
        if "anzahl_module" in analyse:
            bericht.append(f"Betroffene Module: {analyse['anzahl_module']}")
        if "anzahl_ressourcen" in analyse:
            bericht.append(f"Fehlende Ressourcen: {analyse['anzahl_ressourcen']}")
        bericht.append(f"Erlaubte Aenderungen: {analyse['erlaubte_aenderungen']}")
        bericht.append(f"Verbotene Aenderungen: {analyse['verbotene_aenderungen']}")
        bericht.append("")
    
    bericht.append("=" * 70)
    bericht.append("ENDE BERICHT")
    bericht.append("=" * 70)
    
    # Ausgabe
    bericht_text = "\n".join(bericht)
    log("")
    log(bericht_text)
    
    # In Datei schreiben
    os.makedirs(LOG_DIR, exist_ok=True)
    bericht_pfad_out = LOG_DIR / "ALIN_CORE10A_FINDINGS_PRIORISIERUNG_BERICHT.txt"
    with open(bericht_pfad_out, "w", encoding="utf-8") as f:
        f.write(bericht_text)
    log(f"\nBericht geschrieben: {bericht_pfad_out}")
    
    # JSON-Export fuer Weiterverarbeitung
    json_pfad = LOG_DIR / "ALIN_CORE10A_PRIORISIERUNG.json"
    with open(json_pfad, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "priorisierung": priorisierung,
            "analysen": {k: {kk: vv for kk, vv in v.items() if kk != "details"} for k, v in analysen.items()}
        }, f, indent=2, ensure_ascii=False)
    log(f"JSON-Export: {json_pfad}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
