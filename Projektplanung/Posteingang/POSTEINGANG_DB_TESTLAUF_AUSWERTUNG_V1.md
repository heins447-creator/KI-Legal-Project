# Posteingang DB-Testlauf Auswertung V1

## Zweck

Dieses Modul wertet den Testlauf aus, bei dem Dateien aus der bestehenden Dokumententabelle wieder in den Posteingang gelegt und durch die Pipeline geführt wurden.

## Geprüft wird

- welche Dateien aus der Datenbank ausgewählt wurden
- welche Sicherheitsberichte entstanden sind
- welche Sprachberichte entstanden sind
- ob offene Arbeitsdateien im Posteingang liegen
- ob eine Vorzimmer-Arbeitsliste mit offenen Entscheidungen vorliegt

## Ergebnis

Die Auswertung wird geschrieben nach:

`Windows_App\Logs\DB_Testlauf_Auswertung`

Erzeugt werden:

- TXT
- CSV
- JSON

## Leitregel

Nach einem echten Testlauf zählt nicht nur, ob der technische Lauf ohne Fehler endet.

Entscheidend ist, ob danach klar erkennbar ist, welche organisatorische Entscheidung als nächstes erforderlich ist.
