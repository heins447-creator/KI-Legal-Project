# Vorzimmer Kommunikationsparameter V1

## Zweck

Das Vorzimmer erhält eine eigene Parameterstelle für Sprache, Kommunikation, Land, Gericht und Beteiligte.

Der Posteingang hat vorher nur Sicherheit, Dateityp, Sprache und grobe Arbeitsübersetzung vorbereitet. Die inhaltliche Einordnung als Beweis, Entlastung, Aussage, Nachweis oder rechtlich erheblicher Vortrag bleibt nachgelagert.

## Grundmodell

Die Software unterscheidet:

- verfügbare Sprachpakete
- interne Arbeitssprache
- Amtssprache
- Prozeßsprache
- Dokumentensprache
- Kommunikationssprache je Beteiligtem
- Ziel der groben Arbeitsübersetzung
- Sprache aus Anschrift, Land, Postleitzahl oder Textspur

## Schweden Arbeitsrecht

Für die Vorlage `TEMPLATE_SE_ARBEITSRECHT` gilt:

- Staat: Schweden
- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- Standardsprache gerichtlicher Kommunikation: Schwedisch
- Standardsprache Gegenseite: Schwedisch
- Standardsprache gegnerischer Anwalt: Schwedisch
- interne Arbeitssprache Anwalt: Deutsch
- grobe Arbeitsübersetzung: Deutsch

Der einzige systematische Sprachbruch ist die interne deutsche Bearbeitung durch den Anwalt.

## Mandant

Mandantenbezogene Spracheinstellungen werden erst konkretisiert, wenn der Mandant vom Anwalt angenommen wurde.

Bis dahin gibt es nur einen Platzhalter, damit die Software weiß, daß diese Werte später ergänzt werden müssen.

## Änderbarkeit

Alle Vorzimmerparameter sind änderbar.

Das ist notwendig, wenn später feststeht:

- ob geklagt wird
- in welchem Land geklagt wird
- welches Gericht zuständig ist
- welche Sprache ein Beteiligter tatsächlich benutzt
- ob ein Vertreter abweichend kommuniziert

## Tabellen

Angelegt werden:

- `vz_language_package_catalog`
- `vz_communication_context_template`
- `vz_participant_communication_profile`
- `vz_address_language_inference_rule`
- `vz_communication_parameter_audit`

## Starter

Direkter Starter:

`I:\KI_Legal_Project\Scripts\Run_Vorzimmer_Kommunikationsparameter.ps1`

## Grenze

Das Vorzimmer pflegt Parameter.

Es entscheidet nicht über Beweiswert, Entlastungswert, rechtliche Relevanz oder endgültige Aktenzuordnung.
