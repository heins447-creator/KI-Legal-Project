# Sprachkontext V2 Neuanfang

## Zweck

Der Sprachbereich wird neu aufgebaut und ausdrücklich getrennt nach:

1. Systemsprachen
2. Personenprofil
3. Fallprofil
4. Beteiligtenprofil
5. Kommunikationssprache
6. Dokumentensprache
7. tatsächlich erkannter oder gesprochener Sprache
8. Posteingangsregel

Die 24 EU-Amtssprachen sind der verfügbare Sprachkatalog. Daraus folgt nicht, daß jeder Anwalt jede Sprache aktiv annimmt.

## Grundregel für die Software

Die Software muß für Anwalt und Sekretariat Grundeinstellungen führen.

Zu speichern sind insbesondere:

- interne Arbeitssprache
- angenommene Auftragssprachen
- Kommunikationssprachen
- Dokumentprüfsprachen
- Entwurfssprache
- Zielsprachregel für Übersetzungen
- Aktivstatus

Der Anwalt muß auswählen können, in welchen Sprachen er Aufträge annimmt. Alle 24 EU-Amtssprachen stehen zur Auswahl, werden aber nicht automatisch als aktive Annahmesprachen gesetzt.

## Mandantenseite

Mandantenbezogene Spracheinstellungen werden erst angelegt, wenn der Mandant vom Anwalt angenommen wurde.

Vor der Mandatsannahme darf es nur eine Vorlage oder einen Posteingangsvermerk geben, aber kein endgültiges Mandanten-Sprachprofil.

## Fallprofil

Ein Fall hat eigene Sprachwerte.

Zu speichern sind:

- Staat
- Rechtsgebiet
- Landessprache
- Prozesssprache
- interne Arbeitssprache
- Standard-Dokumentensprache
- tatsächlich erwartete Sprache
- Übersetzungsbedarf
- Dolmetscherbedarf

## Beteiligtenprofil

Beteiligte haben eigene Sprachwerte.

Zu unterscheiden sind:

- Gericht
- Mandant
- gegnerischer Anwalt
- Gegenseite
- interne Bearbeitung

Jeder Beteiligte kann eine andere Kommunikationssprache, Dokumentensprache und tatsächliche Sprache haben.

## Beispiel Schweden Arbeitsrecht

Für einen schwedischen Arbeitsrechtsfall gilt als Vorlage:

- Staat: Schweden
- Rechtsgebiet: Arbeitsrecht
- Landessprache: Schwedisch
- Prozesssprache: Schwedisch
- interne Arbeitssprache: Deutsch
- Dokumentensprache: Schwedisch
- Kommunikation mit Gericht: Schwedisch
- Kommunikation mit gegnerischem Anwalt: Englisch möglich
- Gegenseite: Schwedisch
- Mandant: erst nach Mandatsannahme als echtes Mandantenprofil

## Posteingang

Beim Datenimport wird nicht nur eine Sprache gespeichert.

Zu trennen sind:

- erwartete Dokumentensprache
- tatsächlich erkannte Sprache
- Zielarbeitssprache intern
- Prozesssprache
- Kommunikationssprache nach Beteiligtem

Bei Abweichungen erzeugt die Software eine Entscheidungskarte für das Vorzimmer und markiert Übersetzungsbedarf.

## Technische Tabellen V2

Angelegt werden:

- `lang_language_catalog`
- `lang_staff_language_settings`
- `lang_case_language_settings`
- `lang_participant_language_settings`
- `lang_intake_language_rules`
- `lang_language_context_audit`

## Leitregel

Sprache ist kein einzelnes Feld.

Sprache ist ein Kontext aus Person, Fall, Beteiligtem, Dokument, Kommunikation und tatsächlicher Verwendung.
