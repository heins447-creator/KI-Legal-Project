# CORE-16 – Dry-Run Validierung des Migrationsplans

## Zweck

CORE-16 prueft den CORE-15 Migrationsplan auf:
- Zielpfad-Kollisionen
- Quelldatei-Existenz
- SHA-Dubletten im Kopierplan
- Gesperrte Dateien, die kopiert werden sollen

## Eingaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE15_migrationsplan.json`

## Ausgaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE16_dry_run_ergebnis.json`
- `ALIN_Neustart_Core/Reports/CORE16_DRY_RUN_BERICHT.txt`

## Freigabe-Logik

- `dry_run_freigegeben = true` nur wenn **keine kritischen Befunde** vorliegen.
- Wenn kritische Befunde vorliegen, darf CORE-17 **nicht** kopieren.

## Regeln

1. **Nur pruefend** – Keine Dateien werden kopiert.
2. Kritische Befunde blockieren die Migration.
3. Warnungen werden protokolliert, blockieren aber nicht.

## Sicherheit

- `produktiv_freigegeben = false`
- `nur_pruefend = true`

## Abhaengigkeiten

- CORE-15 muss abgeschlossen sein.

## Dateien

- `Scripts/python_runner/core16_dry_run_validierung.py`
- `Scripts/python_runner/check_core16_dry_run_validierung.py`
- `Scripts/CORE16_DRY_RUN_VALIDIERUNG_AUTOLAUF.ps1`
