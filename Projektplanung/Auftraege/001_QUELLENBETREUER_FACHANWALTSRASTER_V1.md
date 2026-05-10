# Auftrag 001: QUELLENBETREUER_FACHANWALTSRASTER_V1

## Ziel

Baue das Grundgerüst für einen Quellenbetreuer, der Rechtsquellen, Sprachquellen und Berufs-/Gerichtsquellen fachgebietsbezogen verwaltet.

Dieser Auftrag ist Voraussetzung für spätere Türschwelle, Sprachpakete und Agentenbearbeitung.

## Fachlicher Ausgangspunkt

Die interne Kanzleistruktur richtet sich an den deutschen Fachanwaltsgebieten aus.

Für diesen ersten Auftrag ist nur aktiv anzulegen:

- Fachanwaltsraster: Arbeitsrecht
- Zielland: Schweden
- Sprache: Schwedisch
- Kanzleisprache: Deutsch
- Paketname: `sv_de_arbeitsrecht_se`
- spätere Dokumenttypen: Arbeitsvertrag und Kündigung

## Nicht tun

Keine Türschwellenmaske programmieren.

Keine endgültige Übersetzung programmieren.

Keine 500 Dateien verarbeiten.

Keine freie Internetrecherche.

Keine echten Mandantendaten verwenden.

Keine große EU-Datenbank importieren.

## Anzulegende Struktur

### Datenbankmigration

Lege eine Migration an:

`Database\Migrations\011_quellenbetreuer_fachanwaltsraster_v1.sql`

Tabellen:

- `source_registry`
- `source_adapter_registry`
- `source_health_check`
- `source_cache_policy`
- `source_change_log`
- `de_specialist_area`
- `country_legal_area_mapping`
- `country_court_route`
- `country_legal_profession`
- `language_package_registry`
- `language_package_source_map`

### Startdaten

Mindestens anlegen:

- deutsches Fachgebiet: Arbeitsrecht
- Land: Schweden
- Sprachpaket: `sv_de_arbeitsrecht_se`
- Quellentypen:
  - EU-Justizportal
  - CCBE
  - EUR-Lex / Cellar / ELI
  - ECLI
  - IATE / VJM
  - DGT-TM
  - EuroVoc
  - nationale Gesetzesquelle Schweden
  - nationale Gerichtsquelle Schweden
  - nationale Anwaltskammer / Berufsquelle Schweden

Noch keine Massendaten laden.

### Python-Läufer

Lege an:

`Scripts\python_runner\046_quellenbetreuer_fachanwaltsraster_v1.py`

Aufgaben:

- Migration anwenden
- Startdaten eintragen
- Cache-Ordner vorbereiten
- Bericht schreiben
- Tabellen prüfen

### Prüfdatei

Lege an:

`Scripts\python_runner\047_check_quellenbetreuer_fachanwaltsraster_v1.py`

Prüfung:

- Tabellen vorhanden
- Fachgebiet Arbeitsrecht vorhanden
- Land Schweden vorhanden
- Sprachpaket `sv_de_arbeitsrecht_se` vorhanden
- Quellenarten vorhanden
- keine Massendaten importiert

### Starter

Lege an:

`Scripts\Run_Quellenbetreuer_Fachanwaltsraster.ps1`

Muß:

- nach `I:\KI_Legal_Project` wechseln
- Python-Läufer starten
- Prüfdatei starten
- Bericht schreiben
- bei Fehler sauber abbrechen
- Einstiegspunkt anzeigen

### Dokumentation

Lege an:

`Projektplanung\Quellen\QUELLENBETREUER_FACHANWALTSRASTER_V1.md`

Inhalt:

- Zweck
- Grenzen
- Quellenrang
- Offline-Fallback
- Cache-Strategie
- Warum keine freie Internetsuche
- Warum zuerst Quellen, danach Türschwelle

## Akzeptanzkriterien

Der Lauf ist nur erfolgreich, wenn:

- Build erfolgreich ist
- Migration erfolgreich ist
- Prüfung erfolgreich ist
- Bericht geschrieben ist
- Git-Status am Ende sauber ist
- Commit erstellt ist
- keine echten Fallunterlagen verwendet wurden
