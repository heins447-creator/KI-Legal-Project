# Phase 0, AP 0.3: pytest-Aufsetzung und tests-Struktur

## Ziel

ALIN bekommt eine feste Teststruktur. Neue Bausteine sollen kuenftig mit pytest-kompatiblen Tests ausgeliefert werden.

## Struktur

- Konfiguration: `pyproject.toml` unter `[tool.pytest.ini_options]`
- Tests: `tests/`
- Runner: `Scripts/python_runner/phase0_ap03_pytest_setup.py`
- Pruefung: `Scripts/python_runner/check_phase0_ap03_pytest_setup.py`
- Starter: `Scripts/Run_PHASE0_AP03_Pytest_Setup.ps1`

## Regeln

- Keine echten Mandantendaten.
- Keine Internetverbindungen.
- Keine Fremd-API-Aufrufe.
- Datenbanktests nur mit temporaeren Datenbanken.
- pytest wird nicht automatisch installiert.

## Status

Die lokale Projektlaufzeit enthaelt aktuell kein pytest. Die Teststruktur ist vorbereitet; die echte pytest-Ausfuehrung wird erst nach kontrollierter Offline-Bereitstellung aus dem Wheelhouse aktiviert.

## Start

```powershell
Scripts\Run_PHASE0_AP03_Pytest_Setup.ps1
```
