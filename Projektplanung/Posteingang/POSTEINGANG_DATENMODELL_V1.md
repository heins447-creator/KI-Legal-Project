# Posteingang Datenmodell V1

## Zweck

Das Datenmodell bildet den technischen und organisatorischen Posteingang einer Kanzlei ab.

Es trennt den unsicheren Eingang vom normalen Dokumentenbestand.

## Tabellen

### posteingang_intake

Haupttabelle für jeden Eingang.

Enthält:

- eindeutige Eingangskennung
- Eingangskanal
- ursprünglichen Dateinamen
- Dateigröße
- SHA256-Hash
- Zwischenablagepfad
- Quarantänepfad
- behaupteten Absender
- geprüften Absenderstatus
- Signaturstatus
- Zertifikatsangaben
- Schadsoftwareprüfstatus
- Dateityp
- erkannte Sprache
- deutsche Kurzsichtung
- erste Dokumentvermutung
- vorläufige Aktenkennung
- Risikostufe
- Entscheidung des Vorzimmers
- Vorlagezustand beim Anwalt
- spätere Freigabe in den normalen Dokumentenbestand

### posteingang_checks

Prüftabelle.

Hier werden einzelne Prüfschritte protokolliert:

- Hashbildung
- Dateityperkennung
- Signaturprüfung
- Zertifikatsprüfung
- Schadsoftwareprüfung
- Archivprüfung
- Sprachprüfung
- Kurzsichtung

### posteingang_decisions

Entscheidungstabelle.

Hier werden Entscheidungen des Vorzimmers oder des Anwalts gespeichert.

Beispiele:

- Rückfrage an Absender
- Datei technisch nicht verwendbar
- Datei sicher und vorlagefähig
- Mandat vorläufig anlegen
- keine Übernahme
- Vorlage an Anwalt

### posteingang_events

Chronologische Ereignistabelle.

Sie dient der Nachvollziehbarkeit.

### posteingang_allowed_research_sources

Vorbereitete Tabelle für vertrauenswürdige Recherchequellen.

Sie ist für spätere Agenten gedacht.

Zulässig sind insbesondere:

- staatliche Quellen
- Gerichte
- Behörden
- Urteilsdatenbanken
- Universitäten
- rechtswissenschaftliche Fakultäten
- juristische Fachverlage
- verwaltungstechnische Fachquellen

## Leitregel

Der Posteingang ist keine normale Dokumentenablage.

Der Posteingang ist ein Sicherheits-, Prüf- und Entscheidungsbereich.
