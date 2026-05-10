# CODING_RULES

## Harte Verbote

Keine Cloud.

Keine GitHub-Verbindung.

Keine Änderungen an `AnythingLLM_Storage`.

Keine langen Skriptkörper direkt im Terminal ausführen.

Keine Commits bei Buildfehler.

Keine gleichzeitigen Großumbauten.

## Erlaubter Arbeitsbereich

Regelmäßig erlaubt:

- `Windows_App\App\MainWindow.xaml`
- `Windows_App\App\MainWindow.xaml.cs`
- `Windows_App\Scripts`
- `Windows_App\Logs`

Nur mit gesondertem Auftrag:

- Projektdateien
- Datenmodell
- externe Bibliotheken
- Datenbankdateien

## Git-Regeln

Vor Beginn:

`git status --short` muß leer sein.

Bei Erfolg:

- Build 0 Fehler
- nur erlaubte Dateien geändert
- Commit mit klarer Nachricht

Bei Fehler:

- Rollback
- Rollback-Build
- kein Commit
- Fehlerprotokoll

## KI-Regeln

Die lokale KI darf nur kleine Änderungsbefehle erzeugen.

Erlaubte Änderungsarten:

- `replace_once`
- `insert_after_once`
- kleine gezielte Ergänzungen

Nicht erlaubt:

- freie Großumbauten
- ganze Dateien ohne Not neu schreiben
- Architekturentscheidung ohne Spezifikation
- Änderungen außerhalb freigegebener Dateien