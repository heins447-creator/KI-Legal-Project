# Posteingang Dokumentsprachprofil V1

## Zweck

Dieses Modul führt die Sprache nicht nur als Bericht, sondern als eigenes Dokument-Sprachprofil.

Damit kann die spätere Softwarebearbeitung bereits wissen:

- welches Dokument welche Primärsprache hat
- ob weitere Sprachen erkannt wurden
- ob das Dokument wahrscheinlich zweisprachig oder mehrsprachig ist
- ob eine grobe Arbeitsübersetzung nach Deutsch erforderlich ist
- welche Sprache als Prozeßsprache und Amtssprache gilt
- welcher Sprachvermerk mit der Dokumentkennung durch die Datenbank läuft

## Datenbank

Angelegt werden:

- `posteingang_document_language_profile`
- `posteingang_document_language_audit`

Wichtige Felder:

- `document_language_id`
- `intake_id`
- `document_key`
- `mandant_key`
- `case_key`
- `detected_primary_language_code`
- `detected_language_codes_json`
- `detected_secondary_language_codes_json`
- `is_multilingual`
- `internal_work_language_code`
- `rough_translation_target_language_code`
- `rough_translation_required`
- `procedural_language_code`
- `official_language_code`
- `language_routing_key`

## Schwedischer Arbeitsrechtsfall

Für den derzeitigen Fall gilt:

- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- grobe Arbeitsübersetzung: Deutsch

## Mehrsprachige Dokumente

Ein Dokument kann mehr als eine erkannte Sprache haben.

Dann bleibt eine Primärsprache gespeichert, weitere Sprachen werden zusätzlich in JSON abgelegt. Die spätere Agentenbearbeitung kann damit genauer arbeiten.

## Grenze des Posteingangs

Der Posteingang entscheidet nicht:

- ob etwas Beweis ist
- ob etwas Entlastung ist
- ob etwas rechtlich erheblich ist
- ob etwas in der Akte welchem Sachverhaltsblock zugeordnet wird

Der Posteingang speichert nur die sprachliche Vorinformation und macht die spätere Arbeit möglich.

## Ergebnisordner

Berichte werden geschrieben nach:

`Windows_App\Logs\Dokumentsprachprofile`

Einzelprofile werden geschrieben nach:

`Posteingang\95_Dokumentsprachprofile`
