# Auftrag 003: QUELLENKANDIDATEN_EU_SE_OFFICIAL_SOURCES_V1

## Ziel

Erzeuge ein strukturiertes Quellenkandidaten- und Quellenklassifizierungsregister für EU-Quellen und schwedische Quellen.

Dieser Baustein erweitert den Quellenbetreuer. Er führt keine freie Internetrecherche aus und lädt keine Massendaten.

## Grundlage

Pflichtkontext lesen:

- AGENTS.md
- Projektplanung\MASTERPROMPT_KI_LEGAL_PROJECT_V1.md
- Projektplanung\CODING_AGENT_CONTEXT_V1.md
- Projektplanung\MASTER_INDEX.md
- Projektplanung\Quellen\QUELLENBETREUER_FACHANWALTSRASTER_V1.md
- Projektplanung\Agenten\AGENTEN_KONTEXT_SKILL_REGISTER_V1.md
- Config\coding_agent_context_v1.json

## Harte Grenzen

Keine echte Internetrecherche.

Keine Massendatenimporte.

Keine API-Schlüssel.

Keine echten Mandantendaten.

Keine Türschwellenmaske.

Keine rechtliche Endbewertung.

## Zu erzeugende Pflichtdateien

1. Database\Migrations\013_quellenkandidaten_eu_se_v1.sql
2. Scripts\python_runner\051_quellenkandidaten_eu_se_v1.py
3. Scripts\python_runner\052_check_quellenkandidaten_eu_se_v1.py
4. Scripts\Run_Quellenkandidaten_EU_SE.ps1
5. Projektplanung\Quellen\QUELLENKANDIDATEN_EU_SE_OFFICIAL_SOURCES_V1.md

## Datenbankinhalt

Lege Tabellen oder Erweiterungen an für:

- source_candidate_registry
- source_candidate_classification
- source_candidate_review_rule
- source_candidate_jurisdiction_map
- source_candidate_language_map

## Startdaten

Mindestens vorbereiten:

- EUR-Lex / ELI / Cellar
- ECLI
- EU-Justizportal
- IATE
- EuroVoc
- DGT Translation Memory
- CCBE
- schwedische Gesetzesquelle als Kandidat
- schwedische Gerichtsquelle als Kandidat
- schwedische Berufs- oder Kammerquelle als Kandidat

## Fachlogik

Jeder Kandidat braucht:

- Quelle
- Quellentyp
- Jurisdiktion
- Land
- Sprache
- Rang
- Rechtsgebietsbezug
- erlaubte spätere Nutzung
- Offline-Strategie
- Cache-Strategie
- Prüfstatus
- Hinweis, daß noch kein Liveabruf erfolgt ist

## Technische Pflicht

Migration, Python-Läufer, Python-Prüfdatei, PowerShell-Starter, Dokumentation und Bericht.

Python- und PowerShell-Syntax müssen gültig sein.

Prüfdatei muß Tabellen und Startdaten prüfen.

.NET-Build darf nicht brechen.

Am Ende Git-Status sauber vorbereiten.