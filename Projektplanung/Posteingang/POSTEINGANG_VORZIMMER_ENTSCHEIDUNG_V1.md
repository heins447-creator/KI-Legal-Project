# Posteingang Vorzimmer-Entscheidung V1

## Zweck

Dieses Modul setzt Vorzimmerentscheidungen technisch um.

Die Vorzimmer-Arbeitsliste zeigt offene Fälle. Die Entscheidung wird nicht frei im Programm geraten, sondern über eine CSV-Datei im Entscheidungsordner vorgegeben.

## Entscheidungsordner

Entscheidungsdateien werden abgelegt unter:

`Windows_App\Logs\Vorzimmer_Entscheidungen`

Die Vorlage liegt zusätzlich unter:

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

## Wirkung

Bei einer Bewegungsentscheidung werden passende Arbeitsdateien in den Zielbereich verschoben.

Nachweisdateien bleiben als Protokoll erhalten.

Verarbeitete Entscheidungsdateien werden nach `Verarbeitet` verschoben.

Fehlerhafte Entscheidungsdateien werden nach `Fehler` verschoben.

## Starter

Der Starter liegt unter:

`Scripts\Run_Vorzimmer_Entscheidung.ps1`

## Leitregel

Die Software führt nur dokumentierte Vorzimmerentscheidungen aus. Sie ersetzt keine anwaltliche Prüfung und keine organisatorische Freigabe.
