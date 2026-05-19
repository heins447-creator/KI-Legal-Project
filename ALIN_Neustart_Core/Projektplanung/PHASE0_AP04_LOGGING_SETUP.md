# Phase 0, AP 0.4: Strukturiertes JSON-Logging

## Ziel

ALIN schreibt technische Ereignisse strukturiert als JSON-Zeilen. Dadurch koennen Healthcheck, Audit-nahe technische Ereignisse und Fehlersuche spaeter maschinell ausgewertet werden.

## Standardpfad

Der Standardpfad ist:

```text
%LocalAppData%\ALIN\Logs
```

Tests duerfen einen temporaeren Logordner uebergeben.

## Modul

`alin_core/logging_config.py` stellt bereit:

- `JsonLineFormatter`
- `get_default_log_dir`
- `configure_json_logging`
- `log_event`

## Regeln

- Keine echten Mandantendaten in technischen Logs.
- Keine Internetverbindung.
- Keine Fremd-API.
- Ein Logeintrag ist eine JSON-Zeile.
- Mindestfelder: `timestamp`, `level`, `logger`, `message`, `module`.

## Start

```powershell
Scripts\Run_PHASE0_AP04_Logging_Setup.ps1
```
