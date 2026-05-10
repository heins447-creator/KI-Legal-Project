# Posteingang Vorzimmer-Entscheidung V1

## Zweck

Dieses Modul setzt dokumentierte Vorzimmerentscheidungen technisch um.

Die Vorzimmer-Arbeitsliste zeigt offene Fälle. Die eigentliche Entscheidung wird nicht durch das Programm geraten, sondern durch eine CSV-Eingabedatei vorgegeben.

## Eingaberegel

Als Eingabe werden nur CSV-Dateien verarbeitet, deren Dateiname mit folgendem Präfix beginnt:

`EINGABE_VORZIMMER_ENTSCHEIDUNG_`

Die Vorlage heißt:

`EINGABE_VORZIMMER_ENTSCHEIDUNG_TEMPLATE.csv`

Ergebnis-CSV-Dateien werden dadurch nicht mehr versehentlich als neue Eingabedateien verarbeitet.

## Entscheidungsordner

Eingabedateien werden abgelegt unter:

`Windows_App\Logs\Vorzimmer_Entscheidungen`

Die allgemeine Vorlage liegt zusätzlich unter:

`Config\vorzimmer_entscheidung_template_v1.csv`

## Spalten der Entscheidungsdatei

- `decision_id`
- `intake_id`
- `source_path`
- `aktion`
- `begruendung`
- `frist`
- `verantwortlich`

Entweder `intake_id` oder `source_path` muß angegeben werden.

## Zulässige Aktionen

- `ANWALTVORLAGE`
- `RUECKFRAGE_ABSENDER`
- `ABWEISEN`
- `SIGNATURPRUEFUNG`
- `SPRACHPRUEFUNG`
- `QUARANTAENE`
- `ARCHIVIEREN`
- `KEINE_AKTION`
- `ZURUECKSTELLEN`

## Ablage der Ergebnisse

- Berichte nach `Windows_App\Logs\Vorzimmer_Entscheidungen\Berichte`
- verarbeitete Eingabe-CSV nach `Windows_App\Logs\Vorzimmer_Entscheidungen\Verarbeitet`
- fehlerhafte Eingabe-CSV nach `Windows_App\Logs\Vorzimmer_Entscheidungen\Fehler`
- Nachweise nach `Windows_App\Logs\Vorzimmer_Entscheidungen\Nachweise`

## Leitregel

Die Software führt nur dokumentierte Vorzimmerentscheidungen aus. Sie ersetzt keine anwaltliche Prüfung und keine organisatorische Freigabe.
