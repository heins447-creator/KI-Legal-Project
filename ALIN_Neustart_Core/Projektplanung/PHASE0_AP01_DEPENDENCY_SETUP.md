# Phase 0, AP 0.1: Dependency-Management und Offline-Wheelhouse

## Ziel

AP 0.1 legt die reproduzierbare Python-Projektgrundlage fuer ALIN an. Die Software bleibt offline-first: Es werden keine Pakete heruntergeladen, keine Installationen ausgelöst und keine externen APIs eingebunden.

## Angelegte Struktur

- `pyproject.toml`: Projektmetadaten, Python-Version und direkt benoetigte Laufzeitpakete.
- `requirements.lock`: erster gepinnter Lock fuer die lokal bereits genutzten Kernpakete.
- `Config/phase0_ap01_dependency_policy_v1.json`: technische Policy fuer Python, uv, Lockfile und Wheelhouse.
- `Wheelhouse/python/README.md`: Regeln fuer den spaeteren Offline-Spiegel.
- `Scripts/python_runner/phase0_ap01_dependency_setup.py`: Laeufer fuer Bericht und Status.
- `Scripts/python_runner/check_phase0_ap01_dependency_setup.py`: Pruefung ohne Internetzugriff.
- `Scripts/Run_PHASE0_AP01_Dependency_Setup.ps1`: PowerShell-Starter.

## Abhaengigkeiten

Der erste Lock enthaelt nur die fuer den vorhandenen Kern direkt relevanten Pakete:

- `duckdb`
- `fastapi`
- `numpy`
- `uvicorn`

Transitive Mindestabhaengigkeiten fuer FastAPI/Uvicorn sind ebenfalls gepinnt. Entwicklungswerkzeuge und Cloud-/API-Clients aus der lokalen Python-Umgebung werden bewusst nicht in den ALIN-Lock uebernommen.

## uv-Status

`uv` ist als Zielwerkzeug festgelegt. In der geprueften lokalen Projektlaufzeit ist `uv` noch nicht installiert. Da Installationen ohne ausdrueckliche Zustimmung verboten sind, bleibt die Bereitstellung des `uv`-Binaries ein kontrollierter Folgeschritt.

## Offline-Installation

Zielbefehl fuer spaetere Offline-Installation:

```powershell
uv pip sync --offline --find-links Wheelhouse/python requirements.lock
```

Dieser Befehl darf erst genutzt werden, wenn `uv` und die Wheels kontrolliert bereitgestellt und geprueft wurden.

## Keine Datenbankmigration

AP 0.1 aendert keine Datenbankstruktur. Eine Migration ist deshalb nicht erforderlich.
