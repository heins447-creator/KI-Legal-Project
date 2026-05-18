#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-26: Roadmap-Dispatcher und Selbstfortsetzung

Ziel:
    Liest die CORE-25 Gesamt-Roadmap, bestimmt die naechste ausfuehrbare Stufe,
    erzeugt einen vollstaendigen Auftrag und schreibt diesen in die CORE-24 Queue.
    Unterstuetzt Selbstfortsetzung durch Status-Tracking.

Lieferpflichten aus AGENTS.md:
    - Python-Laeufer unter Scripts/python_runner/
    - Pruefdatei unter Scripts/python_runner/
    - PowerShell-Starter unter Scripts/
    - Konfiguration unter Config/
    - Dokumentation unter Projektplanung/
    - Testlauf
    - Bericht unter ALIN_Neustart_Core/Reports/
    - Git-Status vor und nach Aenderung
    - Git-Commit nur bei erfolgreichem Build und erfolgreicher Pruefung

Regeln:
    - Keine destruktiven Operationen
    - Keine Unicode-Sonderzeichen in Print-Statements (Windows cp1252)
    - Alle Pfade relativ zu BASE_DIR
    - Sicherheitsgrenzen aus Config einhalten
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
CONFIG_PATH = BASE_DIR / "Config" / "core26_roadmap_dispatcher_v1.json"

# Eingabedateien
ROADMAP_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE25_gesamt_roadmap_v2.json"
DASHBOARD_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE23_dashboard.json"
ARBEITSINDEX_PATH = BASE_DIR / "Config" / "core21_arbeitsindex_v1.json"
AGENTENREGELN_PATH = BASE_DIR / "Config" / "core22_agentenregeln_v1.json"
QUEUE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_auftragsqueue.json"
MAPPING_PATH = BASE_DIR / "ALIN_Neustart_Core" / "09_Automanager" / "CORE27_stufe_zu_core_mapping.json"
REPARATUR_LOG_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_reparatur_log.json"

# Ausgabedateien
STATUS_PATH = BASE_DIR / "ALIN_Neustart_Core" / "09_Automanager" / "CORE26_dispatcher_status.json"
AUFTRAG_PATH = BASE_DIR / "ALIN_Neustart_Core" / "09_Automanager" / "CORE26_naechster_auftrag.json"
BERICHT_PATH = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE26_ROADMAP_DISPATCHER_BERICHT.txt"

GIT_STATUS_VOR_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE26_git_status_vor.txt"
GIT_STATUS_NACH_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE26_git_status_nach.txt"

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================


def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    ts = zeitstempel()
    line = f"[{ts}] {msg}"
    # ASCII-only prints for Windows cp1252 compatibility
    safe_line = line.encode("ascii", "replace").decode("ascii")
    print(safe_line)
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

def lade_mapping_tabelle() -> dict:
    """
    Liest die CORE27 Mapping-Tabelle STUFE-XXX -> CORE-YY.
    """
    if not MAPPING_PATH.exists():
        return {}
    try:
        return lade_json(MAPPING_PATH)
    except Exception:
        return {}


def bestimme_technische_modul_id(stufe_id: str, mapping: dict) -> str:
    """
    Bestimmt die technische Modul-ID fuer eine Stufe.
    - Wenn Stufe kein STUFE-Praefix hat, wird sie unveraendert zurueckgegeben
    - Wenn Stufe STUFE-XXX ist, pruefe Mapping-Tabelle
    - Falls Mapping existiert, verwende gemappte CORE-Nummer
    - Falls kein Mapping existiert, bestimme naechste freie CORE-Nummer
    """
    if not stufe_id.startswith("STUFE-"):
        return stufe_id
    
    eintraege = mapping.get("mapping_eintraege", [])
    for eintrag in eintraege:
        if eintrag.get("stufe_id") == stufe_id:
            return eintrag.get("technische_modul_id", stufe_id)
    
    # Kein Mapping gefunden - bestimme naechste freie Nummer
    # Sammle alle bekannten CORE-Nummern
    existierende = set()
    for eintrag in eintraege:
        tid = eintrag.get("technische_modul_id", "")
        match = re.match(r"CORE-(\d+)", tid)
        if match:
            existierende.add(int(match.group(1)))
    
    # Fuege auch die festen technischen Module hinzu
    for tm in ["CORE-14", "CORE-15", "CORE-16", "CORE-17", "CORE-18",
               "CORE-19", "CORE-20", "CORE-21", "CORE-22", "CORE-23",
               "CORE-24", "CORE-25", "CORE-26", "CORE-27"]:
        match = re.match(r"CORE-(\d+)", tm)
        if match:
            existierende.add(int(match.group(1)))
    
    naechste = max(existierende) + 1 if existierende else 27
    return f"CORE-{naechste}"



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


def git_log_oneline(n: int = 20) -> str:
    rc, out, err = run_cmd(["git", "log", "--oneline", f"-{n}"])
    if rc == 0:
        return out
    return f"FEHLER: {err}"


def bereich_status(pfad_str: str, arbeitsindex: dict) -> str:
    """
    Prueft, ob ein Pfad in aktiv, referenz, gesperrt oder unbekannt faellt.
    """
    pfad_lower = pfad_str.lower().replace("\\", "/")
    bereiche = arbeitsindex.get("bereiche", {})

    # Pruefe gesperrt (Schluesselwoerter)
    for gesperrt in bereiche.get("gesperrt", []):
        if gesperrt.lower() in pfad_lower:
            return "gesperrt"

    # Pruefe aktiv
    for aktiv in bereiche.get("aktiv", []):
        aktiv_norm = aktiv.lower().rstrip("/")
        if pfad_lower.startswith(aktiv_norm):
            return "aktiv"

    # Pruefe referenz
    for referenz in bereiche.get("referenz", []):
        ref_norm = referenz.lower().rstrip("/")
        if pfad_lower.startswith(ref_norm):
            return "referenz"

    return "unbekannt"


# =============================================================================
# A. ROADMAP LESEN
# =============================================================================


def lade_roadmap() -> tuple[dict, list[dict], bool, str]:
    """
    Liest CORE25_gesamt_roadmap.json und gibt die Stufen zurueck.
    """
    if not ROADMAP_PATH.exists():
        return {}, [], False, f"Roadmap nicht gefunden: {ROADMAP_PATH}"

    try:
        data = lade_json(ROADMAP_PATH)
    except Exception as e:
        return {}, [], False, f"Roadmap Lesefehler: {e}"

    stufen = data.get("roadmap", {}).get("stufen", [])
    return data, stufen, True, f"Roadmap geladen: {len(stufen)} Stufen"


def pruefe_zyklische_abhaengigkeiten(stufen: list[dict]) -> tuple[bool, list[str]]:
    """
    DFS-basierte Zyklenerkennung im Abhaengigkeitsgraphen.
    """
    graph = {}
    alle_ids = set()
    for stufe in stufen:
        sid = stufe["stufe_id"]
        alle_ids.add(sid)
        graph[sid] = stufe.get("abhaengigkeiten", [])

    fehlende = []
    for sid, deps in graph.items():
        for dep in deps:
            if dep not in alle_ids:
                fehlende.append(f"{sid} -> {dep} (existiert nicht)")

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


# =============================================================================
# B. PROJEKTSTATUS LESEN
# =============================================================================


def lade_projektstatus() -> tuple[dict, dict, dict, dict, dict, bool, str]:
    """
    Liest Dashboard, Arbeitsindex, Agentenregeln, Queue, Reparatur-Log.
    """
    dashboard = {}
    arbeitsindex = {}
    agentenregeln = {}
    queue = {}
    reparatur_log = {}

    fehler = []

    if DASHBOARD_PATH.exists():
        try:
            dashboard = lade_json(DASHBOARD_PATH)
        except Exception as e:
            fehler.append(f"Dashboard Lesefehler: {e}")
    else:
        fehler.append(f"Dashboard nicht gefunden: {DASHBOARD_PATH}")

    if ARBEITSINDEX_PATH.exists():
        try:
            arbeitsindex = lade_json(ARBEITSINDEX_PATH)
        except Exception as e:
            fehler.append(f"Arbeitsindex Lesefehler: {e}")
    else:
        fehler.append(f"Arbeitsindex nicht gefunden: {ARBEITSINDEX_PATH}")

    if AGENTENREGELN_PATH.exists():
        try:
            agentenregeln = lade_json(AGENTENREGELN_PATH)
        except Exception as e:
            fehler.append(f"Agentenregeln Lesefehler: {e}")
    else:
        fehler.append(f"Agentenregeln nicht gefunden: {AGENTENREGELN_PATH}")

    if QUEUE_PATH.exists():
        try:
            queue = lade_json(QUEUE_PATH)
        except Exception as e:
            fehler.append(f"Queue Lesefehler: {e}")
    else:
        fehler.append(f"Queue nicht gefunden: {QUEUE_PATH}")

    if REPARATUR_LOG_PATH.exists():
        try:
            reparatur_log = lade_json(REPARATUR_LOG_PATH)
        except Exception as e:
            fehler.append(f"Reparatur-Log Lesefehler: {e}")
    else:
        fehler.append(f"Reparatur-Log nicht gefunden: {REPARATUR_LOG_PATH}")

    ok = len(fehler) == 0
    msg = "Alle Projektstatus-Dateien geladen" if ok else f"{len(fehler)} Projektstatus-Fehler"
    return dashboard, arbeitsindex, agentenregeln, queue, reparatur_log, ok, msg


def ermittle_abgeschlossene_stufen(dashboard: dict, stufen: list[dict]) -> set[str]:
    """
    Ermittelt alle abgeschlossenen Stufen.
    - Aus Dashboard: status_core_13_bis_22
    - Aus Roadmap: status == 'abgeschlossen'
    """
    abgeschlossen = set()

    # Aus Dashboard
    status_core = dashboard.get("status_core_13_bis_22", {})
    for core_id, info in status_core.items():
        if info.get("status") == "abgeschlossen":
            abgeschlossen.add(core_id)

    # Aus Roadmap-Stufen
    for stufe in stufen:
        sid = stufe.get("stufe_id", "")
        if stufe.get("status") == "abgeschlossen":
            abgeschlossen.add(sid)

    return abgeschlossen


# =============================================================================
# C. NAECHSTE STUFE BESTIMMEN
# =============================================================================


def ist_stufe_ausfuehrbar(
    stufe: dict,
    abgeschlossen: set[str],
    arbeitsindex: dict,
    agentenregeln: dict
) -> tuple[bool, list[str]]:
    """
    Prueft, ob eine Stufe ausfuehrbar ist.
    Gibt (True/False, [blockade_gruende]) zurueck.
    """
    blockaden = []
    sid = stufe.get("stufe_id", "")
    status = stufe.get("status", "")
    deps = stufe.get("abhaengigkeiten", [])
    sperren = stufe.get("sperren", [])
    eingaben = stufe.get("eingaben", [])
    ausgaben = stufe.get("ausgaben", [])

    # 1. Bereits abgeschlossen?
    if status == "abgeschlossen":
        blockaden.append("bereits abgeschlossen")
        return False, blockaden

    # 2. Gesperrt?
    if status == "gesperrt":
        blockaden.append("Stufe ist gesperrt")
        return False, blockaden

    # 3. Alle Abhaengigkeiten erfuellt?
    for dep in deps:
        if dep not in abgeschlossen:
            blockaden.append(f"Abhaengigkeit nicht erfuellt: {dep}")

    # 4. Sperren pruefen
    for sperre in sperren:
        sperre_lower = sperre.lower()
        if "produktivfreigabe" in sperre_lower or "menschliche freigabe" in sperre_lower:
            blockaden.append(f"Produktivfreigabe erforderlich: {sperre}")
        if "echte daten" in sperre_lower or "mandantendaten" in sperre_lower:
            blockaden.append(f"Echte Daten erforderlich: {sperre}")
        if "cloud" in sperre_lower or "internet" in sperre_lower or "api" in sperre_lower:
            blockaden.append(f"Cloud/Internet/API erforderlich: {sperre}")
        if "db-aenderung" in sperre_lower or "datenbank" in sperre_lower:
            blockaden.append(f"DB-Aenderung erforderlich: {sperre}")

    # 5. Pfadpruefung fuer Eingaben/Ausgaben
    alle_pfade = eingaben + ausgaben
    for pfad in alle_pfade:
        if isinstance(pfad, str):
            status_pfad = bereich_status(pfad, arbeitsindex)
            if status_pfad == "gesperrt":
                blockaden.append(f"Pfad gesperrt: {pfad}")
            elif status_pfad == "unbekannt":
                # Unbekannte Pfade sind kein harter Blocker, aber dokumentieren
                pass

    # 6. Spezifische Stufen, die immer blockiert sind (z.B. CORE-26 selbst als Abschluss)
    if sid == "CORE-26":
        blockaden.append("CORE-26 ist Abschlussstufe, nur manuell")

    return len(blockaden) == 0, blockaden


def finde_naechste_ausfuehrbare_stufe(
    stufen: list[dict],
    abgeschlossen: set[str],
    arbeitsindex: dict,
    agentenregeln: dict
) -> tuple[dict | None, list[dict]]:
    """
    Findet die naechste ausfuehrbare Stufe (nach Prioritaet sortiert).
    Gibt auch alle blockierten Stufen zurueck.
    """
    blockierte = []
    kandidaten = []

    for stufe in stufen:
        ok, gruende = ist_stufe_ausfuehrbar(stufe, abgeschlossen, arbeitsindex, agentenregeln)
        if ok:
            kandidaten.append(stufe)
        else:
            blockierte.append({
                "stufe_id": stufe.get("stufe_id", ""),
                "name": stufe.get("name", ""),
                "blockade_gruende": gruende
            })

    if not kandidaten:
        return None, blockierte

    # Sortiere nach Prioritaet
    kandidaten.sort(key=lambda x: x.get("prioritaet", 999))
    return kandidaten[0], blockierte


# =============================================================================
# D. AUFTRAG ERZEUGEN
# =============================================================================


def erzeuge_auftrag(
    stufe: dict,
    arbeitsindex: dict,
    agentenregeln: dict,
    naechste_stufe_id: str | None
) -> dict:
    """
    Erzeugt einen vollstaendigen Auftrag aus einer Stufe.
    """
    sid = stufe.get("stufe_id", "")
    name = stufe.get("name", "")
    beschreibung = stufe.get("beschreibung", "")
    eingaben = stufe.get("eingaben", [])
    ausgaben = stufe.get("ausgaben", [])
    tests = stufe.get("tests", [])

    # Erlaubte Pfade aus Arbeitsindex
    erlaubte_pfade = arbeitsindex.get("bereiche", {}).get("aktiv", [])

    # Gesperrte Pfade
    gesperrte_pfade = arbeitsindex.get("bereiche", {}).get("gesperrt", [])

    # Rote Linien aus Agentenregeln
    rote_linien = [
        "Keine Loeschung",
        "Keine Verschiebung",
        "Keine Umbenennung alter Dateien",
        "Keine DB-Aenderung",
        "Keine Originalaenderung",
        "Keine echten Mandantendaten",
        "Keine Cloud",
        "Kein Internet",
        "Keine API-Nutzung",
        "Keine Installation",
        "Keine Produktivfreigabe"
    ]

    # Testpflichten
    testpflichten = [
        "py_compile auf allen neuen Python-Dateien",
        "Check-Datei erfolgreich ausfuehren",
        "Runner erfolgreich ausfuehren",
        "Bericht pruefen"
    ]

    # Berichtspflichten
    berichtspflichten = [
        f"ALIN_Neustart_Core/Reports/{technische_id.replace('-', '_')}_BERICHT.txt"
    ]

    auftrag = {
        "auftrags_id": f"AUFTRAG-{sid}-{zeitstempel().replace(':', '')}",
        "stufe_id": sid,
        "name": name,
        "beschreibung": beschreibung,
        "eingaben": eingaben,
        "ausgaben": ausgaben,
        "erlaubte_pfade": erlaubte_pfade,
        "gesperrte_pfade": gesperrte_pfade,
        "rote_linien": rote_linien,
        "testpflichten": testpflichten,
        "berichtspflichten": berichtspflichten,
        "commit_regel": "Nur bei Erfolg, Prefix: CORE-26",
        "folgeentscheidung": naechste_stufe_id,
        "tests_aus_roadmap": tests,
        "erzeugt_am": zeitstempel(),
        "modul": "CORE-26"
    }

    return auftrag


# =============================================================================
# E. QUEUE SCHREIBEN
# =============================================================================


def schreibe_in_queue(auftrag: dict, queue: dict) -> tuple[bool, str]:
    """
    Schreibt den Auftrag in die CORE-24 Queue.
    Respektiert bestehende Struktur.
    """
    if not isinstance(queue, dict):
        queue = {}

    # Fuege Auftrag unter einem neuen Schluessel ein
    auftrags_key = f"auftrag_{auftrag['stufe_id']}"
    if auftrags_key in queue:
        # Falls bereits vorhanden, nummeriere
        counter = 1
        while f"{auftrags_key}_{counter}" in queue:
            counter += 1
        auftrags_key = f"{auftrags_key}_{counter}"

    queue[auftrags_key] = auftrag
    queue["letzter_auftrag"] = auftrags_key
    queue["letztes_update"] = zeitstempel()

    try:
        speichere_json(QUEUE_PATH, queue)
        return True, f"Auftrag in Queue geschrieben: {auftrags_key}"
    except Exception as e:
        return False, f"Queue-Schreibfehler: {e}"


# =============================================================================
# F. AUSFUEHRUNGSMODUS
# =============================================================================


def bestimme_ausfuehrungsmodus(config: dict) -> str:
    """
    Bestimmt den Ausfuehrungsmodus aus Config oder Default.
    """
    modus = config.get("ausfuehrungsmodus", {}).get("standard", "execute_next")
    erlaubt = config.get("ausfuehrungsmodus", {}).get("erlaubte_modi", ["plan_only", "execute_next"])
    if modus not in erlaubt:
        return "plan_only"
    return modus


# =============================================================================
# G. FORTSETZUNG NACH ERFOLG
# =============================================================================


def schreibe_status(
    dispatcher_status: str,
    naechste_stufe: dict | None,
    blockierte: list[dict],
    bericht_zusammenfassung: dict
) -> None:
    """
    Schreibt den Dispatcher-Status fuer die naechste automatische Fortsetzung.
    """
    status = {
        "modul_id": "CORE-26",
        "version": "1.0.0",
        "zeitstempel": zeitstempel(),
        "dispatcher_status": dispatcher_status,
        "naechste_stufe": naechste_stufe.get("stufe_id", "") if naechste_stufe else None,
        "naechste_stufe_name": naechste_stufe.get("name", "") if naechste_stufe else None,
        "blockierte_stufen_anzahl": len(blockierte),
        "blockierte_stufen_ids": [b["stufe_id"] for b in blockierte],
        "bericht_zusammenfassung": bericht_zusammenfassung,
        "fortsetzung_beim_naechsten_lauf": True if naechste_stufe else False
    }
    speichere_json(STATUS_PATH, status)


def schreibe_auftrags_json(auftrag: dict | None) -> None:
    """
    Schreibt den naechsten Auftrag als JSON.
    """
    if auftrag is None:
        auftrag = {"kein_auftrag": True, "zeitstempel": zeitstempel()}
    speichere_json(AUFTRAG_PATH, auftrag)


# =============================================================================
# BERICHTSERSTELLUNG
# =============================================================================


def erzeuge_bericht(
    roadmap_meta: dict,
    stufen_anzahl: int,
    abgeschlossen_ids: set[str],
    blockierte: list[dict],
    naechste_stufe: dict | None,
    auftrag: dict | None,
    queue_geschrieben: bool,
    modus: str,
    technische_blockaden: list[str],
    commit_hash: str
) -> str:
    """
    Erzeugt den menschenlesbaren Bericht.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("CORE-26: ROADMAP-DISPATCHER BERICHT")
    lines.append("=" * 80)
    lines.append(f"Zeitstempel: {zeitstempel()}")
    lines.append(f"Modul: CORE-26 - Roadmap-Dispatcher und Selbstfortsetzung")
    lines.append(f"Version: 1.0.0")
    lines.append("")
    lines.append(f"Commit-Hash: {commit_hash}")
    lines.append("")
    lines.append("ROADMAP-STATUS:")
    lines.append(f"  Roadmap gelesen: JA ({roadmap_meta.get('modul_id', 'unbekannt')})")
    lines.append(f"  Anzahl Stufen: {stufen_anzahl}")
    lines.append("")
    lines.append("ABGESCHLOSSENE STUFEN:")
    for sid in sorted(abgeschlossen_ids):
        lines.append(f"  - {sid}")
    lines.append(f"  Gesamt: {len(abgeschlossen_ids)} Stufen abgeschlossen")
    lines.append("")
    lines.append("BLOCKIERTE STUFEN:")
    for b in blockierte:
        lines.append(f"  - {b['stufe_id']}: {b['name']}")
        for grund in b['blockade_gruende']:
            lines.append(f"      Grund: {grund}")
    lines.append(f"  Gesamt: {len(blockierte)} Stufen blockiert")
    lines.append("")
    lines.append("NAECHSTE AUSGEWAEHLTE STUFE:")
    if naechste_stufe:
        lines.append(f"  Stufe-ID: {naechste_stufe.get('stufe_id', '')}")
        lines.append(f"  Name: {naechste_stufe.get('name', '')}")
        lines.append(f"  Phase: {naechste_stufe.get('phase', '')}")
        lines.append(f"  Prioritaet: {naechste_stufe.get('prioritaet', '')}")
    else:
        lines.append("  KEINE ausfuehrbare Stufe gefunden")
    lines.append("")
    lines.append("ERZEUGTER AUFTRAG:")
    if auftrag:
        lines.append(f"  Auftrags-ID: {auftrag.get('auftrags_id', '')}")
        lines.append(f"  Stufe: {auftrag.get('stufe_id', '')}")
        lines.append(f"  Name: {auftrag.get('name', '')}")
        lines.append(f"  Folgeentscheidung: {auftrag.get('folgeentscheidung', 'keine')}")
    else:
        lines.append("  KEIN Auftrag erzeugt")
    lines.append("")
    lines.append("QUEUE-STATUS:")
    lines.append(f"  Queue-Eintrag geschrieben: {'JA' if queue_geschrieben else 'NEIN'}")
    lines.append("")
    lines.append("AUSFUEHRUNGSMODUS:")
    lines.append(f"  Modus: {modus}")
    lines.append(f"  execute_next gestartet: {'JA' if modus == 'execute_next' else 'NEIN'}")
    lines.append("")
    lines.append("TECHNISCHE BLOCKADEN:")
    if technische_blockaden:
        for tb in technische_blockaden:
            lines.append(f"  - {tb}")
    else:
        lines.append("  Keine technischen Blockaden")
    lines.append("")
    lines.append("FORTSETZUNG:")
    if naechste_stufe:
        lines.append(f"  Naechster automatischer Lauf wird Stufe '{naechste_stufe.get('stufe_id', '')}' bearbeiten")
        lines.append("  Status-JSON und Auftrags-JSON wurden geschrieben")
    else:
        lines.append("  Keine automatische Fortsetzung moeglich - alle Stufen blockiert oder abgeschlossen")
    lines.append("")
    lines.append("=" * 80)
    lines.append("ENDE BERICHT")
    lines.append("=" * 80)
    return "\n".join(lines) + "\n"


# =============================================================================
# HAUPTLOGIK
# =============================================================================


def main() -> int:
    log("=" * 80)
    log("CORE-26: Roadmap-Dispatcher gestartet")
    log("=" * 80)

    # 1. Git-Status vorher
    git_status_speichern(GIT_STATUS_VOR_PATH)
    log(f"Git-Status vorher gespeichert: {GIT_STATUS_VOR_PATH}")

    # 2. Config laden
    config = {}
    if CONFIG_PATH.exists():
        try:
            config = lade_json(CONFIG_PATH)
            log(f"Config geladen: {CONFIG_PATH}")
        except Exception as e:
            log(f"WARNUNG: Config Lesefehler: {e}")
    else:
        log(f"WARNUNG: Config nicht gefunden: {CONFIG_PATH}")

    # 3. Roadmap laden
    roadmap_data, stufen, roadmap_ok, roadmap_msg = lade_roadmap()
    log(roadmap_msg)
    if not roadmap_ok:
        log("FEHLER: Roadmap konnte nicht geladen werden. Abbruch.")
        return 1

    # 4. Zyklenfreiheit pruefen
    zyklen_ok, zyklen_meldungen = pruefe_zyklische_abhaengigkeiten(stufen)
    if not zyklen_ok:
        log("FEHLER: Zyklische Abhaengigkeiten in Roadmap gefunden:")
        for zm in zyklen_meldungen:
            log(f"  {zm}")
        return 1
    log("Roadmap ist zyklenfrei")

    # 5. Projektstatus laden
    dashboard, arbeitsindex, agentenregeln, queue, reparatur_log, status_ok, status_msg = lade_projektstatus()
    log(status_msg)

    # 6. Abgeschlossene Stufen ermitteln
    abgeschlossen = ermittle_abgeschlossene_stufen(dashboard, stufen)
    log(f"Abgeschlossene Stufen: {len(abgeschlossen)}")

    # 7. Git-Log fuer Commits
    git_history = git_log_oneline(20)
    log("Git-Log (letzte 20 Commits) geladen")

    # 8. Naechste ausfuehrbare Stufe finden
    naechste_stufe, blockierte = finde_naechste_ausfuehrbare_stufe(
        stufen, abgeschlossen, arbeitsindex, agentenregeln
    )

    if naechste_stufe:
        log(f"Naechste ausfuehrbare Stufe: {naechste_stufe.get('stufe_id', '')} - {naechste_stufe.get('name', '')}")
    else:
        log("KEINE ausfuehrbare Stufe gefunden")

    # 9. Auftrag erzeugen
    auftrag = None
    naechste_stufe_id = None
    if naechste_stufe:
        # Bestimme Folgeentscheidung (naechste erlaubte Stufe)
        erlaubte_naechste = naechste_stufe.get("erlaubte_naechste_module", [])
        if erlaubte_naechste:
            naechste_stufe_id = erlaubte_naechste[0]

        auftrag = erzeuge_auftrag(naechste_stufe, arbeitsindex, agentenregeln, naechste_stufe_id)
        log(f"Auftrag erzeugt: {auftrag['auftrags_id']}")

    # 10. Ausfuehrungsmodus bestimmen
    modus = bestimme_ausfuehrungsmodus(config)
    log(f"Ausfuehrungsmodus: {modus}")

    # 11. In Queue schreiben (falls execute_next)
    queue_geschrieben = False
    technische_blockaden = []

    if modus == "execute_next" and auftrag is not None:
        ok, msg = schreibe_in_queue(auftrag, queue)
        if ok:
            queue_geschrieben = True
            log(msg)
        else:
            technische_blockaden.append(f"Queue-Schreibfehler: {msg}")
            log(f"FEHLER: {msg}")
    elif modus == "plan_only":
        log("Modus = plan_only: Kein Queue-Eintrag geschrieben")
    else:
        if auftrag is None:
            log("Kein Auftrag erzeugt, daher kein Queue-Eintrag")

    # 12. Technische Blockaden pruefen
    if not arbeitsindex:
        technische_blockaden.append("Arbeitsindex nicht lesbar")
    if not agentenregeln:
        technische_blockaden.append("Agentenregeln nicht lesbar")
    if not dashboard:
        technische_blockaden.append("Dashboard nicht lesbar")

    # 13. Commit-Hash ermitteln
    rc, commit_out, _ = run_cmd(["git", "log", "-1", "--format=%H"])
    commit_hash = commit_out.strip() if rc == 0 else "unbekannt"

    # 14. Bericht erzeugen
    bericht_zusammenfassung = {
        "roadmap_gelesen": roadmap_ok,
        "stufen_anzahl": len(stufen),
        "abgeschlossen_anzahl": len(abgeschlossen),
        "blockiert_anzahl": len(blockierte),
        "naechste_stufe": naechste_stufe.get("stufe_id", "") if naechste_stufe else None,
        "queue_geschrieben": queue_geschrieben,
        "modus": modus,
        "technische_blockaden_anzahl": len(technische_blockaden)
    }

    bericht_text = erzeuge_bericht(
        roadmap_data.get("meta", {}),
        len(stufen),
        abgeschlossen,
        blockierte,
        naechste_stufe,
        auftrag,
        queue_geschrieben,
        modus,
        technische_blockaden,
        commit_hash
    )

    BERICHT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BERICHT_PATH, "w", encoding="utf-8") as f:
        f.write(bericht_text)
    log(f"Bericht geschrieben: {BERICHT_PATH}")

    # 15. Status und Auftrag JSON schreiben
    dispatcher_status = "BEREIT" if naechste_stufe else "BLOCKIERT"
    if technische_blockaden:
        dispatcher_status = "TECHNISCH_BLOCKIERT"

    schreibe_status(dispatcher_status, naechste_stufe, blockierte, bericht_zusammenfassung)
    log(f"Status-JSON geschrieben: {STATUS_PATH}")

    schreibe_auftrags_json(auftrag)
    log(f"Auftrags-JSON geschrieben: {AUFTRAG_PATH}")

    # 16. Git add + commit
    zu_committen = [
        "ALIN_Neustart_Core/09_Automanager/CORE26_dispatcher_status.json",
        "ALIN_Neustart_Core/09_Automanager/CORE26_naechster_auftrag.json",
        "ALIN_Neustart_Core/Reports/CORE26_ROADMAP_DISPATCHER_BERICHT.txt",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE26_git_status_vor.txt",
        "ALIN_Neustart_Core/08_Migration/09_Manifest/CORE26_git_status_nach.txt"
    ]

    ok_add, msg_add = git_add_dateien(zu_committen)
    if ok_add:
        log(f"git add OK: {msg_add}")
        ok_commit, msg_commit = git_commit("CORE-26: Roadmap-Dispatcher und Selbstfortsetzung")
        if ok_commit:
            log(f"git commit OK: {msg_commit}")
        else:
            log(f"git commit FEHLER: {msg_commit}")
    else:
        log(f"git add FEHLER: {msg_add}")

    # 17. Git-Status nachher
    git_status_speichern(GIT_STATUS_NACH_PATH)
    log(f"Git-Status nachher gespeichert: {GIT_STATUS_NACH_PATH}")

    # 18. Abschluss
    log("=" * 80)
    if dispatcher_status == "BEREIT":
        log("CORE-26 ERFOLGREICH abgeschlossen.")
        log(f"Naechste Stufe: {naechste_stufe.get('stufe_id', '')}")
        return 0
    elif dispatcher_status == "BLOCKIERT":
        log("CORE-26 abgeschlossen. Keine ausfuehrbare Stufe gefunden (alle blockiert oder abgeschlossen).")
        return 0
    else:
        log("CORE-26 mit TECHNISCHEN BLOCKADEN abgeschlossen.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
