# CORE-20 – Master-Umbau-Bericht

## Zweck

CORE-20 erstellt den Gesamtbericht fuer den Umbau-Automanager CORE-14 bis CORE-20.

## Eingaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE15_migrationsplan.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE16_dry_run_ergebnis.json`
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE18_neustruktur_validierung.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE19_reste_archiv_sperrplan.json`

## Ausgaben

- `ALIN_Neustart_Core/Reports/CORE20_MASTER_UMBAU_BERICHT.txt`

## Regeln

1. **Nur lesend** – Keine Dateien werden kopiert.
2. Sammelt Ergebnisse aus allen CORE-14 bis CORE-19.
3. Bestimmt Gesamtstatus.

## Sicherheit

- `produktiv_freigegeben = false`

## Abhaengigkeiten

- CORE-14 bis CORE-19 sollten abgeschlossen sein.

## Dateien

- `Scripts/python_runner/core20_master_umbau_bericht.py`
- `Scripts/python_runner/check_core20_master_umbau_bericht.py`
- `Scripts/CORE20_MASTER_UMBAU_BERICHT_AUTOLAUF.ps1`
