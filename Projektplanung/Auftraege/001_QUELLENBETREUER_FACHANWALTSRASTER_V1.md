# Auftrag 001: QUELLENBETREUER_FACHANWALTSRASTER_V1

## Absoluter Arbeitsauftrag

Du bist ein Coding-Agent im lokalen Projektordner:

`I:\KI_Legal_Project`

Du musst echte Dateien im Repository erzeugen. Eine bloße Erklärung ist unzulässig.

Wenn Du keine Dateien erzeugst, ist der Auftrag fehlgeschlagen.

## Ziel

Baue das Grundgerüst für den Quellenbetreuer und das Fachanwaltsraster.

Dieser Baustein ist zwingende Grundlage für spätere Türschwelle, Sprachpakete, Agentenbearbeitung und Offline-Handakte.

## Fachlicher Ausgangspunkt

Interne Kanzleistruktur: deutsche Fachanwaltsgebiete.

Erster aktiver fachlicher Testfall:

- Fachanwaltsraster: Arbeitsrecht
- Zielland: Schweden
- Sprache des Originalrechts: Schwedisch
- Kanzleisprache: Deutsch
- Paketname: `sv_de_arbeitsrecht_se`
- spätere Dokumenttypen: Arbeitsvertrag und Kündigung

## Strikte Grenzen

Keine Türschwellenmaske programmieren.

Keine endgültige Übersetzung programmieren.

Keine 500 Dateien verarbeiten.

Keine freie Internetrecherche.

Keine echten Mandantendaten verwenden.

Keine große EU-Datenbank importieren.

Keine API-Schlüssel schreiben.

Keine rechtliche Endbewertung.

## Pflichtdateien

Du musst mindestens genau diese Dateien erzeugen oder ändern:

1. `Database\Migrations\011_quellenbetreuer_fachanwaltsraster_v1.sql`
2. `Scripts\python_runner\046_quellenbetreuer_fachanwaltsraster_v1.py`
3. `Scripts\python_runner\047_check_quellenbetreuer_fachanwaltsraster_v1.py`
4. `Scripts\Run_Quellenbetreuer_Fachanwaltsraster.ps1`
5. `Projektplanung\Quellen\QUELLENBETREUER_FACHANWALTSRASTER_V1.md`

## Datenbankmigration

Lege eine SQL-Migration an:

`Database\Migrations\011_quellenbetreuer_fachanwaltsraster_v1.sql`

Die Migration muss idempotent sein.

Sie muss mindestens diese Tabellen anlegen, falls sie noch nicht bestehen:

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

Die Tabellen dürfen einfache, robuste Spalten enthalten. Wichtig sind:

- technische Kennung
- Land
- Sprache
- Rechtsgebiet
- Fachanwaltsbezug
- Quellenart
- Quellenrang
- Aktualitätsstatus
- Cache-Status
- Offline-Fallback
- erstellt/geändert Zeitstempel

## Startdaten

Der Python-Läufer muss Startdaten eintragen für:

- deutsches Fachgebiet: Arbeitsrecht
- Zielland: Schweden
- Sprache: Schwedisch
- Kanzleisprache: Deutsch
- Sprachpaket: `sv_de_arbeitsrecht_se`

Quellentypen müssen als Registereinträge vorbereitet werden:

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

## Python-Läufer

Lege an:

`Scripts\python_runner\046_quellenbetreuer_fachanwaltsraster_v1.py`

Pflichten:

- Projektwurzel `I:\KI_Legal_Project` verwenden
- DuckDB-Datei `Database\Legal_Brain.duckdb` verwenden
- Migration anwenden
- Startdaten idempotent eintragen
- Cache-Ordner unter `Data\Sources\Cache` vorbereiten
- Bericht unter `Windows_App\Logs` schreiben
- am Ende klar `OK` oder Fehler ausgeben
- sauberer Abbruch mit Exitcode 0/1

## Prüfdatei

Lege an:

`Scripts\python_runner\047_check_quellenbetreuer_fachanwaltsraster_v1.py`

Prüfung:

- Tabellen vorhanden
- Fachgebiet Arbeitsrecht vorhanden
- Land Schweden vorhanden
- Sprachpaket `sv_de_arbeitsrecht_se` vorhanden
- Quellenarten vorhanden
- keine Massendaten importiert
- Bericht unter `Windows_App\Logs` schreiben
- Exitcode 0 nur bei Erfolg

## PowerShell-Starter

Lege an:

`Scripts\Run_Quellenbetreuer_Fachanwaltsraster.ps1`

Pflichten:

- nach `I:\KI_Legal_Project` wechseln
- `Tools\Python312\python.exe` verwenden
- Python-Läufer starten
- Prüfdatei starten
- Bericht schreiben
- bei Fehler sauber abbrechen
- Einstiegspunkt anzeigen

## Dokumentation

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
- Zusammenhang mit Arbeitsrecht Schweden
- Zusammenhang mit Sprachpaket `sv_de_arbeitsrecht_se`

## Akzeptanzkriterien

Der Auftrag ist nur erfüllt, wenn alle Pflichtdateien existieren und mindestens eine echte Git-Änderung erzeugt wurde.

Eine reine Antwort im Chat ohne Dateierzeugung ist verboten.
