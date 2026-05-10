# Posteingang Betriebsstatus und Produktionslauf V1

## Zweck

Dieser Schritt trennt erstmals sauber zwischen Arbeitsdateien und Nachweisdateien.

Die früheren Testläufe haben gezeigt, daß Protokolle, Sicherheitsberichte und Sprachberichte nicht als störende Altlasten behandelt werden dürfen. Sie sind Nachweise. Offene Arbeit liegt dagegen nur in den Arbeitsordnern des Posteingangs.

## Arbeitsbereiche

Als offene Arbeitsbereiche gelten:

- `00_Roh_Eingang`
- `01_Quarantaene`
- `02_Technisch_Geprueft`
- `03_Vorzimmer_Entscheidung`
- `04_Anwaltvorlage`
- `05_Rueckfrage_Absender`
- `06_Abgewiesen`
- `07_Signaturpruefung`
- `08_Sprachpruefung`

## Nachweisbereiche

Nicht als offene Arbeitsdateien zählen:

- `90_Protokolle`
- `91_Entscheidungskarten`
- `92_Sicherheitsberichte`
- `93_Sprachberichte`
- `99_Archiv_Altlasten`

Diese Dateien dürfen vorhanden bleiben. Sie dokumentieren die Verarbeitung.

## Produktionslauf

Der Produktionsstarter liegt unter:

`Scripts\Run_Posteingang_Pipeline.ps1`

Ablauf:

1. Betriebsstatus vor Verarbeitung
2. Posteingang-Pipeline
3. Betriebsstatus nach Verarbeitung

Neue echte Dateien gehören ausschließlich in:

`Posteingang\00_Roh_Eingang`

Danach kann der Produktionsstarter ausgeführt werden.

## Leitregel

Der aktive Posteingang ist nicht deshalb unrein, weil Nachweise vorhanden sind.

Unrein ist er nur, wenn Arbeitsdateien offen sind, die noch Entscheidung, Prüfung, Rückfrage, Signaturprüfung, Anwaltvorlage oder Abweisung verlangen.
