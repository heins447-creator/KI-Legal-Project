# KI_Legal_Project - Entwicklungskonzept und Arbeitsordnung

Stand: 2026-05-10

Projektpfad: `I:\KI_Legal_Project`

Stabiler Rücksprungpunkt:

`STABIL_DOKUMENTENVORSCHAU_2026-05-10`

Aktueller stabiler App-Stand:

`66d51d2 Dateiauswahl mit Textvorschau verbunden`

Aktueller Bereinigungsstand:

`0aa7ae0 Experimentelle Skripte entfernt`

## 1. Zweck des Projekts

Das Projekt ist eine lokale Windows-Anwendung zur Verwaltung, Sichtung, Vorschau und späteren juristischen Auswertung umfangreicher Dokumentenbestände.

Die Anwendung soll Dateien laden, durchsuchen, anzeigen, klassifizieren und später für Beweismittel- und Schriftsatzarbeit nutzbar machen.

Die Anwendung arbeitet lokal.

Es erfolgt keine Cloud-Anbindung.

Es erfolgt keine GitHub-Verbindung.

## 2. Grundprinzip der Entwicklung

Die Entwicklung erfolgt nicht frei, nicht sprunghaft und nicht über lange Terminal-Fragmente.

Jede Änderung wird in kleine, prüfbare Einzelschritte zerlegt.

Verbindliche Reihenfolge:

1. Konzept
2. Aufgabe
3. technischer Einzelschritt
4. Buildprüfung
5. Funktionstest
6. Git-Commit
7. nächste Aufgabe

Keine Aufgabe darf mehrere unkontrollierte Baustellen gleichzeitig öffnen.

## 3. Harte Regeln

Vor jeder Änderung muß gelten:

`git status --short`

muß leer sein.

Bei jeder Änderung gilt:

- nur erlaubte Dateien ändern
- Build muß mit 0 Fehlern enden
- bei Fehler Rollback
- kein Commit bei Buildfehler
- Logdatei schreiben
- Commit nur nach erfolgreicher technischer Prüfung

## 4. Rollen

Der Nutzer gibt fachliche Ziele, Prioritäten und Abnahmeentscheidungen vor.

ChatGPT übernimmt Architektur, Aufgabenzerlegung, Fehleranalyse und sichere Laufskripte.

Die lokale KI darf nur kleine, kontrollierte Änderungsbefehle erzeugen.

Die Prüfroutine steht über der KI. Maßgeblich sind Build, Git-Status, erlaubte Dateien und Rollbackfähigkeit.

## 5. Aktueller Schwerpunkt

Zuerst wird die Dokumentenbasis stabilisiert:

1. Suchfeld über der Dokumentenliste
2. Filter nach Dateiname, Erweiterung und Pfad
3. TXT-Test mit `Testdokument.txt`
4. Sortierung
5. Datei im Standardprogramm öffnen
6. Metadatenanzeige
7. PDF-Textauszug

Erst danach folgen KI-Klassifikation, Datenmodell und Beweismittelverwaltung.

## 6. Verbotene Arbeitsweise

Nicht mehr zulässig:

- halbe PowerShell-Blöcke im Terminal
- offene `>>`-Eingaben
- manuelle Commits nach Buildfehler
- Weiterarbeiten trotz roter Fehlermeldung
- versehentliches Starten alter Experimentalskripte

Zulässig ist nur:

1. vollständiges Laufskript erstellen
2. Laufskript starten
3. Ergebnis prüfen
4. Commit nur bei Build 0 Fehler