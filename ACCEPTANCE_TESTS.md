# ACCEPTANCE_TESTS

## Allgemeine Abnahme

Jede Aufgabe ist nur erledigt, wenn gilt:

- Git war vor Beginn sauber
- Änderung betrifft nur erlaubte Dateien
- Build läuft mit 0 Fehlern
- App startet
- Funktion ist praktisch prüfbar
- Commit erst nach erfolgreichem Build
- Logdatei wurde geschrieben

## Test Dokumentenvorschau

1. App starten
2. `Dokumente laden`
3. Datei `Testdokument.txt` auswählen
4. Text muß im Vorschau-Bereich erscheinen

## Test nicht unterstützter Dateityp

1. PDF-Datei auswählen
2. Vorschau zeigt Hinweis, daß für diesen Dateityp noch keine Textvorschau vorgesehen ist

## Test Suchfeld

1. App starten
2. `Dokumente laden`
3. Suchfeld mit `Testdokument` befüllen
4. Liste zeigt `Testdokument.txt`
5. Klick zeigt Text in Vorschau

## Test Build

Vor und nach jeder Aufgabe:

`Windows_App\Scripts\Build_App.ps1`

Erwartung:

- 0 Fehler
- keine ungeklärten Warnungen