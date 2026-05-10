# Anwaltvorlage Grundmodul V1

## Zweck

Dieses Modul beginnt den Abschnitt nach dem Posteingang.

Der Posteingang hat bis hierher nur gesichert, geprüft, Sprache erkannt, eine grobe deutsche Arbeitsübersetzung vorbereitet oder markiert und die organisatorische Weitergabe ermöglicht.

Die Anwaltvorlage übernimmt nur formell, was zur anwaltlichen Sichtung bereitsteht.

## Quelle

Ausgewertet wird:

`Posteingang\04_Anwaltvorlage`

Ergänzend werden Nachweise herangezogen aus:

- `Posteingang\92_Sicherheitsberichte`
- `Posteingang\93_Sprachberichte`
- `Posteingang\95_Dokumentsprachprofile`
- `Posteingang\96_Uebersetzung_DE`
- `Posteingang\97_Schlusskontrolle`

## Schweden Arbeitsrecht

Für die Fallvorlage gilt:

- Staat: Schweden
- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- grobe Arbeitsübersetzung: Deutsch
- Beteiligte: Arbeitnehmer gegen kommunalen Arbeitgeber

## Datenbanktabellen

Angelegt werden:

- `anwalt_review_queue`
- `anwalt_review_audit`
- `anwalt_case_context_template`

## Grenze

Dieses Modul entscheidet nicht:

- Beweiswert
- Entlastungswert
- Aussagequalität
- rechtliche Relevanz
- endgültige Aktenzuordnung
- Klageentscheidung

Diese Arbeit beginnt erst in der nachgelagerten Agentenbearbeitung und in der anwaltlichen Prüfung.

## Starter

Direktstart:

`I:\KI_Legal_Project\Scripts\Run_Anwaltvorlage.ps1`
