# CORE-14 – Auswertung der CORE-13 Altbestand-Inventur

## Zweck

CORE-14 liest die Ergebnisse der CORE-13 Altbestand-Inventur und erstellt fuer jede Datei eine **Zielentscheidung** fuer den Umbau unter `ALIN_Neustart_Core/08_Migration`.

## Eingaben

- `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_altbestand_inventur.json`
- `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE13_sperrhinweise.csv`

## Ausgaben

- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.csv`
- `ALIN_Neustart_Core/Reports/CORE14_AUSWERTUNG_BERICHT.txt`

## Zielentscheidungen

| Zielentscheidung | Quell-Klassifikation | Bedeutung |
|---|---|---|
| `UEBERNEHMEN_KOPIEREND` | AKTIV | In die neue Struktur kopieren |
| `NICHT_UEBERNEHMEN_ERSETZT` | ERSETZT | Nicht kopieren, wurde ersetzt |
| `ARCHIV_VORSCHLAG` | ALT_ABER_NOCH_RELEVANT, LOG_BERICHT | Archivierung empfohlen |
| `DUBLETTE_NICHT_KOPIEREN` | DUBLETTE | Dublette, nicht kopieren |
| `TESTREST_NICHT_KOPIEREN` | TESTREST | Testdatei, nicht kopieren |
| `LAUFZEITARTEFAKT_NICHT_KOPIEREN` | LAUFZEIT_ARTEFAKT | Temporaer, nicht kopieren |
| `CONFIG_LOKAL_MANUELL` | CONFIG_LOKAL | Manuelle Pruefung erforderlich |
| `SPERREN_NICHT_KOPIEREN` | SPERREN, oder KRITISCH/HOCH | Gesperrt, nicht kopieren |
| `MANUELL_PRUEFEN` | UNGEKLÄRT | Unklar, manuelle Entscheidung |

## Regeln

1. **Nur lesend** – Keine Dateien werden verschoben, geloescht oder umbenannt.
2. Sperrhinweise mit Schweregrad `KRITISCH` oder `HOCH` setzen die Zielentscheidung auf `SPERREN_NICHT_KOPIEREN`.
3. Die urspruengliche Klassifikation bleibt im Ausgabedatensatz erhalten.

## Sicherheit

- `produktiv_freigegeben = false`
- `nur_lesend = true`
- `nur_musterdaten = true`

## Abhaengigkeiten

- CORE-13 muss abgeschlossen sein.

## Dateien

- `Scripts/python_runner/core14_core13_auswertung.py`
- `Scripts/python_runner/check_core14_core13_auswertung.py`
- `Scripts/CORE14_CORE13_AUSWERTUNG_AUTOLAUF.ps1`
