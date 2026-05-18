# CORE-18 – Validierung der neuen Struktur

## Zweck

CORE-18 prueft, ob alle von CORE-17 kopierten Dateien korrekt im Ziel angekommen sind.

## Eingaben

- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json`

## Ausgaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE18_neustruktur_validierung.json`
- `ALIN_Neustart_Core/Reports/CORE18_NEUSTRUKTUR_VALIDIERUNG_BERICHT.txt`

## Pruefungen

1. Datei existiert im Ziel
2. Dateigroesse stimmt ueberein
3. SHA256 stimmt ueberein

## Regeln

1. **Nur pruefend** – Keine Dateien werden kopiert.
2. Wenn CORE-17 blockiert war, wird ein leeres Ergebnis geschrieben.

## Sicherheit

- `produktiv_freigegeben = false`
- `nur_pruefend = true`

## Abhaengigkeiten

- CORE-17 muss abgeschlossen sein.

## Dateien

- `Scripts/python_runner/core18_neustruktur_validierung.py`
- `Scripts/python_runner/check_core18_neustruktur_validierung.py`
- `Scripts/CORE18_NEUSTRUKTUR_VALIDIERUNG_AUTOLAUF.ps1`
