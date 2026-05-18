# CORE-17 – Kopierende Migration

## Zweck

CORE-17 kopiert Dateien gemaess dem Migrationsplan in die neue Struktur unter `ALIN_Neustart_Core/08_Migration`.

## Eingaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE15_migrationsplan.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE16_dry_run_ergebnis.json`

## Ausgaben

- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json`
- `ALIN_Neustart_Core/Reports/CORE17_KOPIERENDE_MIGRATION_BERICHT.txt`

## Regeln

1. **Nur kopierend** – Keine alten Dateien werden geloescht, verschoben oder umbenannt.
2. Nur Dateien mit `kopieren = true` und `gesperrt = false` werden kopiert.
3. Wenn Dry-Run nicht freigegeben ist, wird die Migration blockiert.
4. Die relative Verzeichnisstruktur wird beibehalten.

## Sicherheit

- `produktiv_freigegeben = false`
- `nur_kopierend = true`

## Abhaengigkeiten

- CORE-15 und CORE-16 muessen abgeschlossen sein.
- CORE-16 muss `dry_run_freigegeben = true` melden.

## Dateien

- `Scripts/python_runner/core17_kopierende_migration.py`
- `Scripts/python_runner/check_core17_kopierende_migration.py`
- `Scripts/CORE17_KOPIERENDE_MIGRATION_AUTOLAUF.ps1`
