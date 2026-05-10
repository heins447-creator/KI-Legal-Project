# RUN_TASK_PLAN

## Ziel

Die weitere Entwicklung erfolgt nicht mehr über manuelle Terminal-Fragmente.

Stattdessen gilt:

1. Aufgabe in `TASK_QUEUE.md`
2. eigenes Laufskript unter `Windows_App\Scripts`
3. Start des Laufskripts
4. Buildprüfung
5. Rollback oder Commit
6. Protokoll

## Nächstes Laufskript

`Windows_App\Scripts\RUN_TASK_Suchfeld_Dokumentenliste.ps1`

Dieses Skript muß:

- Git-Status prüfen
- Sicherung anlegen
- Suchfeld nur ergänzen, wenn nicht vorhanden
- doppelte XAML-Namen verhindern
- Filterlogik ergänzen
- Build prüfen
- bei Fehler zurückrollen
- nach Rollback erneut Build prüfen
- bei Erfolg committen
- App starten
- Log schreiben

## Commit-Nachricht bei Erfolg

`Suchfeld für Dokumentenliste ergänzt`

## Nicht erlaubtes Verhalten

- Commit bei Buildfehler
- unvollständiger Rollback
- Änderung außerhalb erlaubter Dateien
- Weiterarbeiten nach roter Fehlermeldung