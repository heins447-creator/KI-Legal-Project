# Phase 0, AP 0.2: DuckDB-Schema und Migrations-Runner

## Ziel

ALIN bekommt eine lokale DuckDB-Datenbank, deren Struktur nicht frei im Code veraendert wird. Jede Schema-Aenderung laeuft ueber eine nummerierte SQL-Migration.

## Aktive Struktur

- Datenbank: `Database/DuckDB/alin_local.duckdb`
- Migrationen: `Database/Migrations/*.sql`
- Migrationstabelle: `alin_system.schema_migrations`
- Runner: `Scripts/python_runner/phase0_ap02_migration_runner.py`
- Pruefung: `Scripts/python_runner/check_phase0_ap02_migration_runner.py`
- Starter: `Scripts/Run_PHASE0_AP02_Migration_Runner.ps1`

## Erste Migrationen

1. `0001_system_schema.sql`
   - legt `alin_system` an
   - legt `alin_system.schema_migrations` an
   - legt `alin_system.database_metadata` an

2. `0002_audit_foundation.sql`
   - legt `alin_audit` an
   - legt `alin_audit.audit_events` als minimale Audit-Grundlage an

## Schutzregeln

- Standard ist `--dry-run`.
- Echte Anwendung braucht `--execute`.
- Bereits angewendete Migrationen werden mit SHA-256 geprueft.
- Geaenderte bereits angewendete Migrationen fuehren zum Abbruch.
- `08_Migration/` bleibt Altbestand und wird nicht aktiv beschrieben.

## Ausfuehrung

Dry-run:

```powershell
Scripts\Run_PHASE0_AP02_Migration_Runner.ps1
```

Echte Anwendung:

```powershell
Scripts\Run_PHASE0_AP02_Migration_Runner.ps1 -Execute
```

Die Pruefdatei benutzt zusaetzlich eine temporaere Testdatenbank unter `Windows_App/Logs` und beruehrt die produktive Datenbank dabei nicht.
