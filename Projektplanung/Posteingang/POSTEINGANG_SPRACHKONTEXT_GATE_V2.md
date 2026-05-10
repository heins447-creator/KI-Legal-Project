# Posteingang Sprachkontext Gate V2

## Zweck

Dieses Modul verbindet den Posteingang mit dem neu aufgebauten Sprachkontext V2.

Die Sicherheitsprüfung bleibt vorgeschaltet. Es werden nur Dateien aus `Posteingang/02_Technisch_Geprueft` sprachlich bewertet.

Dateien aus `Posteingang/07_Signaturpruefung` werden nicht automatisch sprachlich weiterverarbeitet, weil dort zuerst die Signaturfrage geklärt werden muß.

## Trennung der Sprachwerte

Die Software unterscheidet im Posteingang:

- erwartete Dokumentensprache
- tatsächlich erkannte Sprache
- interne Arbeitssprache
- Prozeßsprache
- Kommunikationssprache nach Beteiligtem
- Übersetzungsbedarf
- Dolmetscherbedarf

## Beispiel Schweden Arbeitsrecht

Bei der Vorlage `TEMPLATE_SE_ARBEITSRECHT` gilt:

- Landessprache: Schwedisch
- Prozeßsprache: Schwedisch
- erwartete Dokumentensprache: Schwedisch
- interne Arbeitssprache: Deutsch
- Kommunikation mit gegnerischem Anwalt: Englisch möglich
- Gericht: Schwedisch
- Gegenseite: Schwedisch
- Mandant: erst nach Mandatsannahme als eigenes Mandantenprofil

## Arbeitsweise V2

V2 nimmt noch keine vollwertige KI-Spracherkennung vor.

V2 erzeugt eine erste regelbasierte Sprachsichtung anhand einfacher Textmerkmale. Das genügt für die Schleuse:

- passend
- abweichend
- unklar

Bei Abweichung oder Unklarheit entsteht eine Entscheidungskarte für das Vorzimmer.

## Ergebnisdateien

Das Modul erzeugt:

- Protokoll in `Posteingang/90_Protokolle`
- CSV-Nachweis in `Posteingang/90_Protokolle`
- JSONL-Nachweis in `Posteingang/90_Protokolle`
- Sprachbericht in `Posteingang/93_Sprachberichte`
- Sprachkarte für das Vorzimmer in `Posteingang/03_Vorzimmer_Entscheidung`

## Leitregel

Die Software darf nicht nur fragen, welche Sprache ein Dokument hat.

Sie muß fragen, in welchem Sprachkontext das Dokument steht.
