# Quellenkandidaten EU SE Official Sources V1

## Zweck

Dieser Baustein erweitert den Quellenbetreuer um ein strukturiertes Quellenkandidaten- und Quellenklassifizierungsregister für EU-Quellen und schwedische Quellen.

Er legt die Grundlage für die spätere Prüfung, Freigabe und Integration von Quellen in den Quellenbetreuer.

## Grenzen

Dieser Baustein führt keine freie Internetrecherche aus. Er lädt keine Massendaten. Er verarbeitet keine echten Mandantendaten. Er erstellt keine Türschwellenmaske, keine endgültige Übersetzung und keine rechtliche Endbewertung.

## Tabellen

- `source_candidate_registry` – Kandidatenregister mit Quelle, Typ, Jurisdiktion, Land, Sprache, Rang, Rechtsgebietsbezug, erlaubter Nutzung, Offline- und Cache-Strategie, Prüfstatus.
- `source_candidate_classification` – Klassifikation der Kandidaten (z. B. Quellentyp).
- `source_candidate_review_rule` – Prüfregeln für Kandidaten (z. B. kein Liveabruf).
- `source_candidate_jurisdiction_map` – Zuordnung von Jurisdiktionen zu Kandidaten.
- `source_candidate_language_map` – Zuordnung von Sprachen zu Kandidaten.

## Startdaten

Folgende Kandidaten werden vorbereitet:

- EUR-Lex / Cellar / ELI
- ECLI
- EU-Justizportal
- IATE
- EuroVoc
- DGT Translation Memory
- CCBE
- Schwedische Gesetzesquelle (Kandidat)
- Schwedische Gerichtsquelle (Kandidat)
- Schwedische Berufs- oder Kammerquelle (Kandidat)

Jeder Kandidat erhält einen Rang, eine erlaubte Nutzung (`terminologie_oder_rechtsquelle`), eine Offline-Strategie (`nicht_vorhanden`), eine Cache-Strategie (`metadaten_und_auszuege`) und einen Prüfstatus (`vorbereitet`).

## Zusammenhang mit Quellenbetreuer

Die Kandidaten ergänzen die bestehenden Quellenregister (`source_registry`, `source_adapter_registry` usw.) um eine Vorbereitungsstufe. Erst nach erfolgreicher Prüfung und Freigabe können Kandidaten in die aktiven Quellenregister übernommen werden.

## Technische Pflicht

- Migration: `Database\Migrations\013_quellenkandidaten_eu_se_v1.sql`
- Python-Läufer: `Scripts\python_runner\051_quellenkandidaten_eu_se_v1.py`
- Python-Prüfdatei: `Scripts\python_runner\052_check_quellenkandidaten_eu_se_v1.py`
- PowerShell-Starter: `Scripts\Run_Quellenkandidaten_EU_SE.ps1`
- Dokumentation: `Projektplanung\Quellen\QUELLENKANDIDATEN_EU_SE_OFFICIAL_SOURCES_V1.md`
