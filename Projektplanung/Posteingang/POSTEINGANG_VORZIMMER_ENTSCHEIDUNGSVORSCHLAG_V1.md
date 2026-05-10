# Posteingang Vorzimmer-Entscheidungsvorschlag V1

## Zweck

Dieses Modul erzeugt aus der letzten Vorzimmer-Arbeitsliste einen Entscheidungsvorschlag.

Es führt keine Entscheidung aus.

## Wichtig

Die erzeugte CSV wird nicht in den ausführenden Entscheidungsordner gelegt, sondern in:

`Windows_App\Logs\Vorzimmer_Entscheidungen\Entwuerfe`

Dadurch kann sie nicht versehentlich durch `Run_Vorzimmer_Entscheidung.ps1` verarbeitet werden.

## Vorschlagslogik

- Quarantäne mit aktiver oder ausführbarer Datei: Abweisung
- Quarantäne mit unklarem Dateityp: Rückfrage an Absender
- Signaturbereich: Signaturprüfung
- Sprachprüfung: Sprachprüfung
- Rückfragebereich: Rückfrage an Absender
- Vorzimmerbereich: Anwaltvorlage, außer bei Signatur- oder Sprachhinweis
- Technisch geprüft: Anwaltvorlage
- Anwaltvorlage: keine Aktion
- Abgewiesen: Archivieren

## Leitregel

Die Software darf Vorschläge machen. Die Entscheidung bleibt organisatorisch beim Vorzimmer und fachlich beim Anwalt.
