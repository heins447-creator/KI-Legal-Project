# Posteingang Bereinigung V1

## Zweck

Diese Bereinigung entfernt Test- und Altlasten aus dem aktiven Posteingang.

Der Posteingang soll als Sicherheits-, Prüf- und Entscheidungsbereich leer und kontrolliert starten. Alte Versuchsdaten stören die Prüfung, weil sie bei Sprachprüfung, Sicherheitsprüfung und Entscheidungskarten erneut auftauchen können.

## Bereinigungsumfang

Die Bereinigung betrifft:

- aktive Testdateien im Posteingang
- erzeugte Testprotokolle im Posteingang
- alte Entscheidungskarten
- alte Sicherheitsberichte
- alte Sprachberichte
- alte Sprachversuche der ersten Sprachmodelle
- alte Datenbanktabellen aus verworfenen Sprachmodellen

## Nicht gelöscht

Nicht gelöscht werden:

- Git-Platzhalter `.gitkeep`
- `README_POSTEINGANG.md`
- Archivordner `Posteingang/99_Archiv_Altlasten`
- produktive Sprachkontext-V2-Tabellen
- produktive Quelltexte
- Migrationsdateien des aktuellen Standes

## Datenbankregel

Aus der Datenbank werden nur eindeutig erkennbare Test- und Altlasten aus sicheren Posteingangs-Lauftabellen entfernt.

Treffer in nicht eindeutig freigegebenen Tabellen werden nur berichtet, aber nicht automatisch gelöscht.

## Leitregel

Versuchsdaten gehören nicht in den aktiven Posteingang.

Neue echte Dateien müssen wieder durch den Posteingang laufen.
