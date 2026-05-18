# CORE-19 – Reste-/Archiv-/Sperrplan

## Zweck

CORE-19 erstellt Plaene fuer alle Dateien, die **nicht** kopiert wurden:
- Reste (sonstige nicht-kopierte Dateien)
- Archiv (archivwuerdige Dateien)
- Gesperrt (Sperrhinweise)
- Testreste
- Laufzeit-Artefakte
- Dubletten
- Manuell zu pruefende Dateien

## Eingaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.json`
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json`

## Ausgaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE19_reste_archiv_sperrplan.json`
- `ALIN_Neustart_Core/Reports/CORE19_RESTE_ARCHIV_SPERRPLAN_BERICHT.txt`

## Regeln

1. **Nur planend** – Keine Dateien werden kopiert.
2. Bereits kopierte Dateien werden ausgeschlossen.
3. Kategorisierung nach Zielentscheidung.

## Sicherheit

- `produktiv_freigegeben = false`
- `nur_planend = true`

## Abhaengigkeiten

- CORE-14 und CORE-17 muessen abgeschlossen sein.

## Dateien

- `Scripts/python_runner/core19_reste_archiv_sperrplan.py`
- `Scripts/python_runner/check_core19_reste_archiv_sperrplan.py`
- `Scripts/CORE19_RESTE_ARCHIV_SPERRPLAN_AUTOLAUF.ps1`
