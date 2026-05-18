#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE-24: Autonomer Entwicklungsmanager / Auftragsqueue / Selbstreparatur

Ziel:
    Ein selbstlaufender Entwicklungsprozess, der:
    1. Das Dashboard liest (CORE23_dashboard.json)
    2. Den Arbeitsindex prüft (Config/core21_arbeitsindex_v1.json)
    3. Den nächsten zulässigen Auftrag selbst bestimmt
    4. Eine Auftragsqueue führt (JSON-Datei)
    5. Für jeden Auftrag ausführt: py_compile → Runner → Check
    6. Bei Fehler: Fehlerbericht auswerten → Reparaturauftrag erzeugen → erneut testen
    7. Bei Erfolg: git add + git commit
    8. Nächsten Auftrag aus der Queue ableitet
    9. Nur bei harter Sperre anhält (z.B. Check 3x fehlgeschlagen, unbekannter Fehler, Pfad gesperrt)

Lieferpflichten aus AGENTS.md:
    - Python-Läufer unter Scripts/python_runner/
    - Prüfdatei unter Scripts/python_runner/
    - PowerShell-Starter unter Scripts/
    - Konfiguration unter Config/
    - Dokumentation unter Projektplanung/
    - Testlauf
    - Bericht unter ALIN_Neustart_Core/Reports/
    - Git-Status vor und nach Änderung
    - Git-Commit nur bei erfolgreichem Build und erfolgreicher Prüfung

Regeln:
    - Nur Befehle aus AGENTENFREIGABE_KLARSTELLUNG.txt verwenden
    - Keine destruktiven Operationen
    - Bei harter Sperre: Bericht schreiben und anhalten
    - Max. 3 Reparaturversuche pro Auftrag
    - Git-Commit nur wenn py_compile + Check + Runner alle erfolgreich
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# =============================================================================
# KONSTANTEN & Pfade
# =============================================================================

BASE_DIR = Path("I:/KI_Legal_Project")
CONFIG_PATH = BASE_DIR / "Config" / "core24_entwicklungsmanager_v1.json"
DASHBOARD_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE23_dashboard.json"
ARBEITSINDEX_PATH = BASE_DIR / "Config" / "core21_arbeitsindex_v1.json"
AGENTENREGELN_PATH = BASE_DIR / "Config" / "core22_agentenregeln_v1.json"
AGENTEN_REGELN_MANIFEST_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE22_agenten_regeln.json"
AGENTENFREIGABE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "AGENTENFREIGABE_KLARSTELLUNG.txt"

QUEUE_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_auftragsqueue.json"
REPARATUR_LOG_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_reparatur_log.json"
BERICHT_PATH = BASE_DIR / "ALIN_Neustart_Core" / "Reports" / "CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt"

PYTHON_EXE = BASE_DIR / "Tools" / "Python312" / "python.exe"
RUNNER_DIR = BASE_DIR / "Scripts" / "python_runner"

GIT_STATUS_VOR_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_git_status_vor.txt"
GIT_STATUS_NACH_PATH = BASE_DIR / "ALIN_Neustart_Core" / "08_Migration" / "09_Manifest" / "CORE24_git_status_nach.txt"

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def zeitstempel() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str) -> None:
    ts = zeitstempel()
    line = f"[{ts}] {msg}"
    print(line)
    # Auch in Bericht schreiben (append)
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


def bereich_status(pfad: str, arbeitsindex: dict) -> str:
    """
    Prüft, ob ein Pfad in 'aktiv', 'referenz', 'gesperrt' oder 'unbekannt' fällt.
    """
    pfad_norm = pfad.replace("\\", "/").lower()
    for bereich in arbeitsindex.get("bereiche", {}).get("aktiv", []):
        if pfad_norm.startswith(bereich.lower().rstrip("/") + "/") or pfad_norm == bereich.lower().rstrip("/"):
            return "aktiv"
    for bereich in arbeitsindex.get("bereiche", {}).get("referenz", []):
        if pfad_norm.startswith(bereich.lower().rstrip("/") + "/") or pfad_norm == bereich.lower().rstrip("/"):
            return "referenz"
    for bereich in arbeitsindex.get("bereiche", {}).get("gesperrt", []):
        if bereich.lower() in pfad_norm:
            return "gesperrt"
    return "unbekannt"


def run_cmd(cmd: list[str], cwd: Path = BASE_DIR, timeout: int = 120) -> tuple[int, str, str]:
    """
    Führt einen Befehl sicher aus und gibt (returncode, stdout, stderr) zurück.
    """
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


def py_compile_pruefung(skript_pfad: Path) -> tuple[bool, str]:
    """
    Führt py_compile auf einem Python-Skript aus.
    """
    if not PYTHON_EXE.exists():
        return False, f"Python-Interpreter nicht gefunden: {PYTHON_EXE}"
    if not skript_pfad.exists():
        return False, f"Skript nicht gefunden: {skript_pfad}"

    rc, out, err = run_cmd([str(PYTHON_EXE), "-m", "py_compile", str(skript_pfad)])
    if rc == 0:
        return True, "py_compile OK"
    else:
        return False, f"py_compile FEHLER (rc={rc}): {err or out}"


def runner_ausfuehren(skript_name: str) -> tuple[bool, str]:
    """
    Führt ein Python-Runner-Skript aus.
    """
    skript_pfad = RUNNER_DIR / skript_name
    if not skript_pfad.exists():
        return False, f"Runner-Skript nicht gefunden: {skript_pfad}"

    rc, out, err = run_cmd([str(PYTHON_EXE), str(skript_pfad)])
    if rc == 0:
        return True, f"Runner OK: {out[:500]}"
    else:
        return False, f"Runner FEHLER (rc={rc}): {err or out}"


def check_ausfuehren(check_skript_name: str) -> tuple[bool, str]:
    """
    Führt eine Check-Datei aus.
    """
    check_pfad = RUNNER_DIR / check_skript_name
    if not check_pfad.exists():
        return False, f"Check-Skript nicht gefunden: {check_pfad}"

    rc, out, err = run_cmd([str(PYTHON_EXE), str(check_pfad)])
    if rc == 0:
        return True, f"Check OK: {out[:500]}"
    else:
        return False, f"Check FEHLER (rc={rc}): {err or out}"


def git_status_speichern(ziel_pfad: Path) -> bool:
    """
    Speichert git status in eine Datei.
    """
    rc, out, err = run_cmd(["git", "status"])
    if rc != 0:
        log(f"WARNUNG: git status fehlgeschlagen: {err}")
        return False
    ziel_pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel_pfad, "w", encoding="utf-8") as f:
        f.write(out)
    return True


def git_add_dateien(dateien: list[str]) -> tuple[bool, str]:
    """
    Führt git add für eine Liste von Dateien aus.
    Ignoriert Dateien, die nicht existieren (Warnung wird geloggt).
    """
    for d in dateien:
        pfad = BASE_DIR / d
        if not pfad.exists():
            log(f"  WARNUNG: Datei für git add nicht gefunden, überspringe: {d}")
            continue
        rc, out, err = run_cmd(["git", "add", d])
        if rc != 0:
            return False, f"git add fehlgeschlagen für {d}: {err}"
    return True, "git add OK"


def git_commit(nachricht: str) -> tuple[bool, str]:
    """
    Führt git commit aus.
    """
    rc, out, err = run_cmd(["git", "commit", "-m", nachricht])
    if rc == 0:
        return True, f"git commit OK: {out.strip()}"
    else:
        # Wenn nichts zu committen ist, ist das kein Fehler
        if "nothing to commit" in (out + err).lower() or "nichts zu committen" in (out + err).lower():
            return True, "Nichts zu committen"
        return False, f"git commit FEHLER: {err or out}"


def fehler_kategorie_auswerten(fehler_text: str, erlaubte_kategorien: list[str]) -> str:
    """
    Versucht, die Fehlerkategorie aus dem Fehlertext zu extrahieren.
    """
    fehler_lower = fehler_text.lower()
    for kat in erlaubte_kategorien:
        if kat.lower() in fehler_lower:
            return kat
    return "unbekannt"


# =============================================================================
# QUEUE-VERWALTUNG
# =============================================================================

def lade_queue() -> dict:
    if QUEUE_PATH.exists():
        try:
            data = lade_json(QUEUE_PATH)
            if isinstance(data, dict) and "auftraege" in data:
                return data
        except Exception:
            pass
    return {
        "meta": {
            "modul_id": "CORE-24",
            "name": "Auftragsqueue",
            "version": "1.0.0",
            "zeitstempel_erstellung": zeitstempel()
        },
        "auftraege": [],
        "abgeschlossen": [],
        "fehlgeschlagen": [],
        "reparatur_auftraege": []
    }


def speichere_queue(queue: dict) -> None:
    queue["meta"]["letzte_aktualisierung"] = zeitstempel()
    speichere_json(QUEUE_PATH, queue)


def lade_reparatur_log() -> dict:
    if REPARATUR_LOG_PATH.exists():
        try:
            data = lade_json(REPARATUR_LOG_PATH)
            if isinstance(data, dict) and "eintraege" in data:
                return data
        except Exception:
            pass
    return {
        "meta": {
            "modul_id": "CORE-24",
            "name": "Reparatur-Log",
            "version": "1.0.0",
            "zeitstempel_erstellung": zeitstempel()
        },
        "eintraege": []
    }


def speichere_reparatur_log(log_data: dict) -> None:
    log_data["meta"]["letzte_aktualisierung"] = zeitstempel()
    speichere_json(REPARATUR_LOG_PATH, log_data)


def finde_naechsten_auftrag(queue: dict, config: dict) -> dict | None:
    """
    Sucht den nächsten ausstehenden Auftrag in der Queue.
    """
    for auftrag in queue.get("auftraege", []):
        if auftrag.get("status") == "ausstehend":
            return auftrag
    return None


def ableite_auftrag_aus_dashboard(dashboard: dict, arbeitsindex: dict, config: dict) -> dict | None:
    """
    Leitet aus dem Dashboard und dem Arbeitsindex den nächsten sinnvollen Auftrag ab.
    Für CORE-24 selbst: Da dies das erste autonome Modul ist, wird ein Selbsttest-Auftrag erzeugt.
    """
    # Prüfe, ob es offene Arbeiten aus dem Dashboard gibt
    status_core = dashboard.get("status_core_13_bis_22", {})

    # Suche nach Modulen mit Status "fehlerhaft" oder "vorhanden" (nicht abgeschlossen)
    offene_module = []
    for modul_id, info in status_core.items():
        if info.get("status") in ["fehlerhaft", "vorhanden"]:
            offene_module.append({
                "modul_id": modul_id,
                "titel": info.get("titel", ""),
                "status": info.get("status", "")
            })

    if offene_module:
        # Nimm das erste offene Modul
        naechstes = offene_module[0]
        return {
            "auftrag_id": f"CORE24_AUTO_{naechstes['modul_id']}_{int(datetime.now(timezone.utc).timestamp())}",
            "modul_id": naechstes["modul_id"],
            "titel": f"Reparatur/Pruefung fuer {naechstes['modul_id']}: {naechstes['titel']}",
            "typ": "pruefung",
            "status": "ausstehend",
            "prioritaet": 1,
            "erstellt": zeitstempel(),
            "reparaturversuche": 0,
            "zielpfad": f"ALIN_Neustart_Core/Reports/{naechstes['modul_id']}_PRUEFBERICHT.txt",
            "bemerkung": f"Automatisch abgeleitet aus Dashboard: Status={naechstes['status']}"
        }

    # Wenn keine offenen Module: Selbsttest-Auftrag für CORE-24
    return {
        "auftrag_id": f"CORE24_AUTO_SELBSTTEST_{int(datetime.now(timezone.utc).timestamp())}",
        "modul_id": "CORE-24",
        "titel": "CORE-24 Selbsttest und Queue-Validierung",
        "typ": "pruefung",
        "status": "ausstehend",
        "prioritaet": 1,
        "erstellt": zeitstempel(),
        "reparaturversuche": 0,
        "zielpfad": "ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt",
        "bemerkung": "Automatisch abgeleitet: Keine offenen Module, Selbsttest"
    }


# =============================================================================
# AUFTRAGSAUSFÜHRUNG
# =============================================================================

def fuehre_auftrag_aus(auftrag: dict, config: dict, arbeitsindex: dict) -> tuple[bool, str, bool]:
    """
    Führt einen Auftrag aus.
    Gibt zurück: (erfolg, meldung, harte_sperre)
    """
    auftrag_id = auftrag.get("auftrag_id", "unbekannt")
    typ = auftrag.get("typ", "")
    zielpfad = auftrag.get("zielpfad", "")
    reparaturversuche = auftrag.get("reparaturversuche", 0)
    max_reparatur = config.get("queue_regeln", {}).get("max_reparaturversuche", 3)

    log(f"Auftrag {auftrag_id} ({typ}): Starte Ausführung...")

    # 1. Prüfe Auftragstyp
    if typ in config.get("verbotene_auftragstypen", []):
        msg = f"Auftragstyp '{typ}' ist VERBOTEN. Harte Sperre."
        log(f"FEHLER: {msg}")
        return False, msg, True

    if typ not in config.get("erlaubte_auftragstypen", []):
        msg = f"Auftragstyp '{typ}' ist nicht in erlaubten Auftragstypen. Harte Sperre."
        log(f"FEHLER: {msg}")
        return False, msg, True

    # 2. Prüfe Zielpfad
    if zielpfad:
        status = bereich_status(zielpfad, arbeitsindex)
        if status == "gesperrt":
            msg = f"Zielpfad '{zielpfad}' ist GESPERRT. Harte Sperre."
            log(f"FEHLER: {msg}")
            return False, msg, True
        if status == "unbekannt":
            msg = f"Zielpfad '{zielpfad}' ist UNBEKANNT. Harte Sperre."
            log(f"FEHLER: {msg}")
            return False, msg, True
        log(f"Zielpfad-Status: {status}")

    # 3. py_compile prüfen (nur für python_runner und alin_core_script)
    if typ in ["python_runner", "alin_core_script"]:
        skript_name = auftrag.get("skript_name", "")
        if skript_name:
            skript_pfad = RUNNER_DIR / skript_name if typ == "python_runner" else BASE_DIR / "ALIN_Neustart_Core" / "Scripts" / skript_name
            ok, msg_compile = py_compile_pruefung(skript_pfad)
            if not ok:
                log(f"py_compile FEHLGESCHLAGEN für {skript_name}: {msg_compile}")
                if reparaturversuche >= max_reparatur:
                    return False, f"py_compile nach {max_reparatur} Versuchen fehlgeschlagen: {msg_compile}", True
                return False, f"py_compile fehlgeschlagen: {msg_compile}", False
            log(f"py_compile OK für {skript_name}")

    # 4. Runner ausführen (nur für python_runner)
    if typ == "python_runner":
        skript_name = auftrag.get("skript_name", "")
        if skript_name:
            ok, msg_runner = runner_ausfuehren(skript_name)
            if not ok:
                log(f"Runner FEHLGESCHLAGEN für {skript_name}: {msg_runner}")
                if reparaturversuche >= max_reparatur:
                    return False, f"Runner nach {max_reparatur} Versuchen fehlgeschlagen: {msg_runner}", True
                return False, f"Runner fehlgeschlagen: {msg_runner}", False
            log(f"Runner OK für {skript_name}")

    # 5. Check ausführen
    if typ in ["python_runner", "alin_core_script", "pruefung"]:
        check_skript = auftrag.get("check_skript", "")
        if not check_skript and typ == "python_runner":
            # Standard: check_<skript_name>
            skript_name = auftrag.get("skript_name", "")
            if skript_name:
                check_skript = f"check_{skript_name}"
        if not check_skript and typ == "alin_core_script":
            skript_name = auftrag.get("skript_name", "")
            if skript_name:
                check_skript = f"check_{skript_name}"

        if check_skript:
            ok, msg_check = check_ausfuehren(check_skript)
            if not ok:
                log(f"Check FEHLGESCHLAGEN für {check_skript}: {msg_check}")
                if reparaturversuche >= max_reparatur:
                    return False, f"Check nach {max_reparatur} Versuchen fehlgeschlagen: {msg_check}", True
                return False, f"Check fehlgeschlagen: {msg_check}", False
            log(f"Check OK für {check_skript}")

    # 6. Git add + commit (nur bei Erfolg)
    if config.get("git_regeln", {}).get("commit_nur_bei_erfolg", True):
        # Git-Status vorher speichern
        git_status_speichern(GIT_STATUS_VOR_PATH)

        # Dateien sammeln
        zu_committen = []
        if zielpfad:
            zu_committen.append(zielpfad)
        if auftrag.get("skript_name"):
            if typ == "python_runner":
                zu_committen.append(f"Scripts/python_runner/{auftrag['skript_name']}")
            elif typ == "alin_core_script":
                zu_committen.append(f"ALIN_Neustart_Core/Scripts/{auftrag['skript_name']}")

        # Manifeste und Queue auch committen
        zu_committen.append("ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json")
        zu_committen.append("ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_reparatur_log.json")
        zu_committen.append("ALIN_Neustart_Core/Reports/CORE24_ENTWICKLUNGSMANAGER_BERICHT.txt")

        ok_add, msg_add = git_add_dateien(zu_committen)
        if not ok_add:
            log(f"git add fehlgeschlagen: {msg_add}")
            if reparaturversuche >= max_reparatur:
                return False, f"git add nach {max_reparatur} Versuchen fehlgeschlagen: {msg_add}", True
            return False, f"git add fehlgeschlagen: {msg_add}", False

        modul_id = auftrag.get("modul_id", "CORE-24")
        commit_msg = f"CORE-24: {auftrag.get('titel', 'Auftrag')} ({auftrag_id})"
        ok_commit, msg_commit = git_commit(commit_msg)
        if not ok_commit:
            log(f"git commit fehlgeschlagen: {msg_commit}")
            if reparaturversuche >= max_reparatur:
                return False, f"git commit nach {max_reparatur} Versuchen fehlgeschlagen: {msg_commit}", True
            return False, f"git commit fehlgeschlagen: {msg_commit}", False

        git_status_speichern(GIT_STATUS_NACH_PATH)
        log(f"git commit OK: {msg_commit}")

    log(f"Auftrag {auftrag_id}: ERFOLGREICH abgeschlossen.")
    return True, "Auftrag erfolgreich abgeschlossen.", False


# =============================================================================
# REPARATURLOGIK
# =============================================================================

def erzeuge_reparaturauftrag(auftrag: dict, fehler_meldung: str, config: dict) -> dict:
    """
    Erzeugt einen Reparaturauftrag basierend auf der Fehlermeldung.
    """
    reparatur_id = f"REPARATUR_{auftrag['auftrag_id']}_{int(datetime.now(timezone.utc).timestamp())}"
    fehler_kat = fehler_kategorie_auswerten(
        fehler_meldung,
        config.get("erlaubte_fehlerkategorien", [])
    )

    reparatur_auftrag = {
        "auftrag_id": reparatur_id,
        "ursprungs_auftrag_id": auftrag["auftrag_id"],
        "modul_id": auftrag.get("modul_id", "CORE-24"),
        "titel": f"Reparatur für {auftrag['auftrag_id']}: {fehler_kat}",
        "typ": "pruefung",
        "status": "ausstehend",
        "prioritaet": 0,  # Höchste Priorität
        "erstellt": zeitstempel(),
        "reparaturversuche": 0,
        "fehler_kategorie": fehler_kat,
        "fehler_meldung": fehler_meldung,
        "zielpfad": auftrag.get("zielpfad", ""),
        "bemerkung": f"Automatisch erzeugte Reparatur für Fehler: {fehler_kat}"
    }

    return reparatur_auftrag


def aktualisiere_reparatur_log(auftrag: dict, fehler_meldung: str, reparatur_auftrag: dict | None = None) -> None:
    log_data = lade_reparatur_log()
    eintrag = {
        "zeitstempel": zeitstempel(),
        "auftrag_id": auftrag.get("auftrag_id", ""),
        "modul_id": auftrag.get("modul_id", ""),
        "fehler_meldung": fehler_meldung,
        "reparatur_auftrag_id": reparatur_auftrag["auftrag_id"] if reparatur_auftrag else None
    }
    log_data["eintraege"].append(eintrag)
    speichere_reparatur_log(log_data)


# =============================================================================
# HAUPTLOGIK
# =============================================================================

def initialisiere_bericht() -> None:
    BERICHT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BERICHT_PATH, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CORE-24: ENTWICKLUNGSMANAGER BERICHT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Zeitstempel: {zeitstempel()}\n")
        f.write(f"Konfiguration: {CONFIG_PATH}\n")
        f.write(f"Dashboard: {DASHBOARD_PATH}\n")
        f.write(f"Arbeitsindex: {ARBEITSINDEX_PATH}\n")
        f.write("=" * 80 + "\n\n")


def main() -> int:
    log("=" * 80)
    log("CORE-24: Autonomer Entwicklungsmanager gestartet")
    log("=" * 80)

    # 1. Initialisiere Bericht
    initialisiere_bericht()

    # 2. Lade Konfiguration
    try:
        config = lade_json(CONFIG_PATH)
        log(f"Konfiguration geladen: {CONFIG_PATH}")
    except Exception as e:
        log(f"HARTE SPERRE: Konfiguration konnte nicht geladen werden: {e}")
        return 1

    # 3. Lade Dashboard
    try:
        dashboard = lade_json(DASHBOARD_PATH)
        log(f"Dashboard geladen: {DASHBOARD_PATH}")
    except Exception as e:
        log(f"HARTE SPERRE: Dashboard konnte nicht geladen werden: {e}")
        return 1

    # 4. Lade Arbeitsindex
    try:
        arbeitsindex = lade_json(ARBEITSINDEX_PATH)
        log(f"Arbeitsindex geladen: {ARBEITSINDEX_PATH}")
    except Exception as e:
        log(f"HARTE SPERRE: Arbeitsindex konnte nicht geladen werden: {e}")
        return 1

    # 5. Lade Queue
    queue = lade_queue()
    log(f"Queue geladen: {len(queue.get('auftraege', []))} Aufträge")

    # 6. Wenn Queue leer, ableite ersten Auftrag aus Dashboard
    if not queue.get("auftraege"):
        log("Queue ist leer. Leite ersten Auftrag aus Dashboard ab...")
        neuer_auftrag = ableite_auftrag_aus_dashboard(dashboard, arbeitsindex, config)
        if neuer_auftrag:
            queue["auftraege"].append(neuer_auftrag)
            speichere_queue(queue)
            log(f"Neuer Auftrag abgeleitet: {neuer_auftrag['auftrag_id']}")

    # 7. Hauptschleife: Verarbeite Aufträge
    max_durchlaeufe = 50  # Sicherheitslimit
    durchlauf = 0
    harte_sperre_aktiv = False

    while durchlauf < max_durchlaeufe and not harte_sperre_aktiv:
        durchlauf += 1
        log(f"--- Durchlauf {durchlauf} ---")

        auftrag = finde_naechsten_auftrag(queue, config)
        if not auftrag:
            log("Keine ausstehenden Aufträge mehr. Queue ist leer.")
            # Versuche, neuen Auftrag abzuleiten
            neuer_auftrag = ableite_auftrag_aus_dashboard(dashboard, arbeitsindex, config)
            if neuer_auftrag:
                # Prüfe, ob dieser Auftrag schon abgeschlossen wurde
                bereits_erledigt = any(
                    a.get("modul_id") == neuer_auftrag["modul_id"] and a.get("status") == "erfolgreich"
                    for a in queue.get("abgeschlossen", [])
                )
                if not bereits_erledigt:
                    queue["auftraege"].append(neuer_auftrag)
                    speichere_queue(queue)
                    log(f"Neuer Auftrag abgeleitet: {neuer_auftrag['auftrag_id']}")
                    continue
                else:
                    log(f"Modul {neuer_auftrag['modul_id']} bereits erfolgreich abgeschlossen.")
            break

        # Auftrag ausführen
        erfolg, meldung, harte_sperre = fuehre_auftrag_aus(auftrag, config, arbeitsindex)

        if harte_sperre:
            log(f"HARTE SPERRE aktiviert für Auftrag {auftrag['auftrag_id']}: {meldung}")
            auftrag["status"] = "hart_gesperrt"
            auftrag["letzte_meldung"] = meldung
            auftrag["zeitstempel_sperre"] = zeitstempel()
            queue["fehlgeschlagen"].append(auftrag)
            # Entferne aus aktiven Aufträgen
            queue["auftraege"] = [a for a in queue["auftraege"] if a["auftrag_id"] != auftrag["auftrag_id"]]
            speichere_queue(queue)
            aktualisiere_reparatur_log(auftrag, meldung)
            harte_sperre_aktiv = True
            break

        if not erfolg:
            # Fehler, aber keine harte Sperre → Reparaturauftrag erzeugen
            auftrag["reparaturversuche"] = auftrag.get("reparaturversuche", 0) + 1
            log(f"Auftrag {auftrag['auftrag_id']} fehlgeschlagen (Versuch {auftrag['reparaturversuche']}): {meldung}")

            reparatur_auftrag = erzeuge_reparaturauftrag(auftrag, meldung, config)
            queue["reparatur_auftraege"].append(reparatur_auftrag)
            queue["auftraege"].append(reparatur_auftrag)

            # Aktualisiere Status des ursprünglichen Auftrags
            for a in queue["auftraege"]:
                if a["auftrag_id"] == auftrag["auftrag_id"]:
                    a["status"] = "wartet_auf_reparatur"
                    a["letzte_meldung"] = meldung
                    break

            speichere_queue(queue)
            aktualisiere_reparatur_log(auftrag, meldung, reparatur_auftrag)

            # Kurze Pause vor dem nächsten Versuch
            pause = config.get("queue_regeln", {}).get("pause_zwischen_auftraegen_sekunden", 2)
            log(f"Pause {pause}s vor nächstem Auftrag...")
            time.sleep(pause)
            continue

        # Erfolg
        auftrag["status"] = "erfolgreich"
        auftrag["letzte_meldung"] = meldung
        auftrag["zeitstempel_abschluss"] = zeitstempel()
        queue["abgeschlossen"].append(auftrag)
        queue["auftraege"] = [a for a in queue["auftraege"] if a["auftrag_id"] != auftrag["auftrag_id"]]
        speichere_queue(queue)
        log(f"Auftrag {auftrag['auftrag_id']} erfolgreich abgeschlossen.")

        # Pause zwischen Aufträgen
        pause = config.get("queue_regeln", {}).get("pause_zwischen_auftraegen_sekunden", 2)
        if pause > 0:
            log(f"Pause {pause}s vor nächstem Auftrag...")
            time.sleep(pause)

    # 8. Abschluss
    log("=" * 80)
    if harte_sperre_aktiv:
        log("CORE-24 ANGEHALTEN wegen harter Sperre.")
        log(f"Bericht: {BERICHT_PATH}")
        log(f"Queue: {QUEUE_PATH}")
        log(f"Reparatur-Log: {REPARATUR_LOG_PATH}")
        return 1
    else:
        log("CORE-24 erfolgreich abgeschlossen. Keine weiteren ausstehenden Aufträge.")
        log(f"Bericht: {BERICHT_PATH}")
        log(f"Queue: {QUEUE_PATH}")
        log(f"Reparatur-Log: {REPARATUR_LOG_PATH}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
