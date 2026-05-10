# Posteingang Sprachgate V1

## Zweck

Das Sprachgate verbindet den technischen Posteingang mit der Sprachlogik der Kanzlei-Software.

Es entscheidet nicht über den Inhalt des Falles. Es erzeugt ein Sprachprofil für den weiteren Datenimport.

## Grundsatz

Die Sprache eines eingehenden Dokuments ist nicht automatisch die interne Arbeitssprache.

Die Landessprache ist nicht automatisch die Sprache der Kommunikation mit der Gegenseite.

Die Prozeßsprache ist gesondert zu führen.

## Verarbeitete Bereiche

Das Sprachgate arbeitet auf bereits technisch geprüften oder zur Signaturprüfung vorgemerkten Dateien.

Es verarbeitet:

- `Posteingang/02_Technisch_Geprueft`
- `Posteingang/07_Signaturpruefung`

Nicht verarbeitet werden normale Quarantänedateien.

## Erkannte Mindestlogik

Für V1 werden einfache Sprachanhaltspunkte erkannt.

Besonders berücksichtigt werden:

- Deutsch
- Englisch
- Schwedisch

Bei Schweden-Arbeitsrecht wird als Vorlage gesetzt:

- Land: Schweden
- Landessprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- mögliche Kommunikation mit gegnerischem Anwalt: Englisch
- Übersetzung erforderlich: ja

## Datenbank

Die Ergebnisse werden in `posteingang_language_profiles` gespeichert.

Damit erhält der spätere Import eine belastbare Grundlage für:

- Übersetzung
- Aktenanlage
- gerichtliche Verfahrenssprache
- interne Bearbeitungssprache
- Kommunikationssprache

## Grenze von V1

V1 ist keine vollwertige automatische Sprachwissenschaft.

V1 ist ein sicherer, protokollierter Anfangspunkt. Unsichere Erkennungen bleiben als unsicher sichtbar.
