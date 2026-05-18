# CORE-15 – Migrationsplan mit Zielpfaden

## Zweck

CORE-15 liest die CORE-14 Auswertung und erstellt fuer jede Datei einen konkreten **Zielpfad** unter `ALIN_Neustart_Core/08_Migration`.

## Eingaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.json`

## Ausgaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE15_migrationsplan.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE15_migrationsplan.csv`
- `ALIN_Neustart_Core/Reports/CORE15_MIGRATIONSPLAN_BERICHT.txt`

## Zielordner-Mapping

| Zielentscheidung | Zielordner |
|---|---|
| `UEBERNEHMEN_KOPIEREND` | `02_Kopierte_Dateien` |
| `MANUELL_PRUEFEN` | `03_Manuell_Pruefen` |
| `SPERREN_NICHT_KOPIEREN` | `04_Gesperrt` |
| `DUBLETTE_NICHT_KOPIEREN` | `05_Dubletten` |
| `TESTREST_NICHT_KOPIEREN` | `06_Testreste` |
| `LAUFZEITARTEFAKT_NICHT_KOPIEREN` | `07_Laufzeit_Artefakte` |
| `ARCHIV_VORSCHLAG` | `08_Archiv_Vorschlag` |
| `NICHT_UEBERNEHMEN_ERSETZT` | `08_Archiv_Vorschlag` |
| `CONFIG_LOKAL_MANUELL` | `03_Manuell_Pruefen` |

## Regeln

1. **Nur planend** – Keine Dateien werden kopiert.
2. Die relative Verzeichnisstruktur wird im Ziel beibehalten.
3. Konflikte (gleicher Zielpfad) werden protokolliert.

## Sicherheit

- `produktiv_freigegeben = false`
- `nur_planend = true`

## Abhaengigkeiten

- CORE-14 muss abgeschlossen sein.

## Dateien

- `Scripts/python_runner/core15_migrationsplan.py`
- `Scripts/python_runner/check_core15_migrationsplan.py`
- `Scripts/CORE15_MIGRATIONSPLAN_AUTOLAUF.ps1`
