# CORE-26: Roadmap-Dispatcher und Selbstfortsetzung

## Zweck

CORE-26 ist der Roadmap-Dispatcher fuer ALIN_Neustart_Core. Er liest die programmierbare Gesamt-Roadmap (CORE-25), bestimmt die naechste ausfuehrbare Stufe, erzeugt einen vollstaendigen Auftrag und schreibt diesen in die CORE-24 Queue. Er unterstuetzt Selbstfortsetzung durch Status-Tracking.

## Funktion

Der Dispatcher verbindet die Roadmap (CORE-25) mit dem autonomen Entwicklungsmanager (CORE-24). Er uebernimmt die Rolle eines "Auftragsplaners", der entscheidet, welche Stufe als naechstes bearbeitet werden soll.

## Ablauf

1. **Roadmap lesen**: Liest `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_gesamt_roadmap.json` mit allen 90 Stufen
2. **Projektstatus lesen**: Liest Dashboard (CORE-23), Arbeitsindex (CORE-21), Agentenregeln (CORE-22), Queue (CORE-24), Reparatur-Log (CORE-24)
3. **Abgeschlossene Stufen ermitteln**: Kombiniert Dashboard-Status mit Roadmap-Status
4. **Zyklenfreiheit pruefen**: DFS-basierte Pruefung des Abhaengigkeitsgraphen
5. **Naechste Stufe bestimmen**: Prueft Ausfuehrbarkeitskriterien (Abhaengigkeiten, Sperren, Pfade)
6. **Auftrag erzeugen**: Vollstaendiger Auftrag mit Ziel, Eingaben, Ausgaben, Pfaden, Testpflichten
7. **Queue schreiben**: Eintrag in `CORE24_auftragsqueue.json`
8. **Status schreiben**: Dispatcher-Status fuer naechsten Lauf
9. **Bericht erzeugen**: Menschenlesbarer Bericht in `ALIN_Neustart_Core/Reports/`
10. **Git-Commit**: Nur bei Erfolg

## Ein-/Ausgaben

### Eingaben
- `Config/core26_roadmap_dispatcher_v1.json` - Konfiguration
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_gesamt_roadmap.json` - Roadmap
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json` - Dashboard
- `Config/core21_arbeitsindex_v1.json` - Arbeitsindex
- `Config/core22_agentenregeln_v1.json` - Agentenregeln
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json` - Queue
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_reparatur_log.json` - Reparatur-Log

### Ausgaben
- `ALIN_Neustart_Core/09_Automanager/CORE26_dispatcher_status.json` - Dispatcher-Status
- `ALIN_Neustart_Core/09_Automanager/CORE26_naechster_auftrag.json` - Naechster Auftrag
- `ALIN_Neustart_Core/Reports/CORE26_ROADMAP_DISPATCHER_BERICHT.txt` - Bericht
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json` - Aktualisierte Queue

## Sicherheitsgrenzen

- Keine Loeschung
- Keine Verschiebung
- Keine Umbenennung alter Dateien
- Keine DB-Aenderung
- Keine Originalaenderung
- Keine echten Mandantendaten
- Keine Cloud
- Kein Internet
- Keine API-Nutzung
- Keine Installation
- Keine Produktivfreigabe

## Ausfuehrungsmodi

- `plan_only`: Nur naechsten Auftrag ermitteln und schreiben
- `execute_next`: Auftrag ermitteln und in Queue schreiben (Standard)

## Dateien

- `Config/core26_roadmap_dispatcher_v1.json` - Konfiguration
- `Scripts/python_runner/core26_roadmap_dispatcher.py` - Python-Runner
- `Scripts/python_runner/check_core26_roadmap_dispatcher.py` - Pruefdatei
- `Scripts/CORE26_ROADMAP_DISPATCHER_AUTOLAUF.ps1` - PowerShell-Starter
- `Projektplanung/CORE26_ROADMAP_DISPATCHER.md` - Dokumentation

## Abhaengigkeiten

- CORE-24 (Autonomer Entwicklungsmanager)
- CORE-25 (Programmierbare Gesamt-Roadmap)
- CORE-23 (Projekt-Dashboard)
- CORE-21 (Arbeitsindex)
- CORE-22 (Agentenregeln)
