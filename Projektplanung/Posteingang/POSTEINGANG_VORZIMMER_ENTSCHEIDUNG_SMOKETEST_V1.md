# Posteingang Vorzimmer-Entscheidung Smoketest V1

## Zweck

Der Smoketest prüft, ob die Vorzimmerentscheidung nicht nur ohne Eingabe läuft, sondern echte Entscheidungsdateien verarbeitet.

## Testfälle

Der Test erzeugt vier künstliche Arbeitsdateien:

1. technisch geprüfte Datei
2. Signaturfall
3. Quarantänefall
4. Sprachkarte

Dazu wird eine Eingabe-CSV mit vier Vorzimmerentscheidungen erzeugt.

## Erwartung

- technisch geprüfte Datei nach `04_Anwaltvorlage`
- Signaturfall nach `05_Rueckfrage_Absender`
- Quarantänefall nach `06_Abgewiesen`
- Sprachkarte nach `08_Sprachpruefung`

Zusätzlich müssen Verarbeitungsnachweise entstehen.

## Bereinigung

Alle Testdateien werden danach unter `Posteingang\99_Archiv_Altlasten` archiviert.

Der aktive Posteingang darf nach dem Smoketest keine Testdateien mehr enthalten.
