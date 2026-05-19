# Phase 0, AP 0.5: Rote Linien als technische Blocker

## Ziel

Die roten Linien aus dem Arbeitsauftrag werden nicht nur dokumentiert, sondern maschinell pruefbar gemacht.

## Dateien

- Regeln: `.alin/redlines.json`
- Schema: `.alin/redlines.schema.json`
- Modul: `alin_core/redline_guard.py`
- Starter: `Scripts/Run_PHASE0_AP05_Redline_Guard.ps1`

## Blockierte Muster

- Pfade ausserhalb der Arbeitswurzel
- echte Mandantendaten
- automatische Internetverbindungen
- Cloud, Telemetrie, Fremd-API
- Datenbankaenderung ohne Migration
- KI-Uebersetzung nach Mandatsannahme
- stille Uebernahme von Triage in die Akte
- Entscheidung ohne Audit-Spur
- Auslieferung ohne Tests
- Tuerschwelle vor Quellenregister, Fachanwaltsraster, Quellenbetreuer, Adapter, Cache und Offline-Fallback

## Start

```powershell
Scripts\Run_PHASE0_AP05_Redline_Guard.ps1
```
