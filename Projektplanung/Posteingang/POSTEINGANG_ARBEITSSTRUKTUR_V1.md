# Posteingang Arbeitsstruktur V1

Der Posteingang ist der vorgelagerte Sicherheits- und Entscheidungsbereich der Kanzlei-Software.

Er ist keine normale Dokumentenablage. Fremde Dateien werden zuerst technisch erfasst, geprüft und einer Vorzimmerentscheidung zugeführt.

## Ordner

- `Posteingang/00_Roh_Eingang` für neue Eingänge
- `Posteingang/01_Quarantaene` für gesperrte oder unklare Dateien
- `Posteingang/02_Technisch_Geprueft` für technisch freigegebene Dateien
- `Posteingang/03_Vorzimmer_Entscheidung` für Entscheidungskarten
- `Posteingang/04_Anwaltvorlage` für spätere anwaltliche Vorlage
- `Posteingang/05_Rueckfrage_Absender` für Rückfragen
- `Posteingang/06_Abgewiesen` für zurückgewiesene Eingänge
- `Posteingang/90_Protokolle` für Nachweise
- `Posteingang/91_Entscheidungskarten` als Reservebereich

## Leitregel

Keine ungeprüfte Datei wird unmittelbar in den normalen Dokumentenbestand übernommen.
