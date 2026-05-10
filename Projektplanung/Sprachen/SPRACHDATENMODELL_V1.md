# Sprachdatenmodell V1

## Tabellen

## app_languages

Enthält alle 24 Amtssprachen der Europäischen Union.

Zweck:
- Systemweite Sprachliste
- Auswahlgrundlage für Rollen und Fälle
- keine Beschränkung auf aktuell verwendete Sprachen

## software_language_settings

Enthält die Grundeinstellung der Software.

Zweck:
- Standardsprache der Oberfläche
- interne Standardsprache
- Rückfallsprache für Übersetzung
- Pflicht zur fallbezogenen Sprachentscheidung

## role_language_settings

Enthält die Arbeitssprache je Rolle.

Rollen:
- Anwalt
- Sekretariat

## role_mandate_languages

Enthält, in welchen Sprachen ein Anwalt Mandate annimmt und in welchen Sprachen Kommunikation vorbereitet werden kann.

Alle 24 Sprachen sind vorhanden. Die Auswahl erfolgt über Werte je Sprache.

## case_language_profiles

Enthält das Sprachprofil des einzelnen Falles.

Beispiel:
- Schweden
- Arbeitsrecht
- Landessprache Schwedisch
- Prozeßsprache Schwedisch
- interne Arbeitssprache Deutsch
- Kommunikation mit gegnerischem Anwalt Englisch

## posteingang_language_profiles

Verknüpft den Posteingang mit einer Sprachentscheidung.

Zweck:
- deklarierte Sprache
- erkannte Sprache
- zuständige Gerichtssprache
- Übersetzungsbedarf
- Sicherheit der Erkennung

## Grundsatz

Sprachentscheidung ist Teil des Datenimports und nicht bloße Anzeigeeinstellung.
