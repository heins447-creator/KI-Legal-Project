# UI08 – Posteingang / Importstrecke – Visuelle Arbeitsübersicht

## Zweck

UI08 bietet eine **visuelle Arbeitsübersicht** über die bestehende Posteingang-Infrastruktur (KM04–KM21). Es liest DuckDB-Tabellen, JSON-Karten und CSV-Listen ein und zeigt den aktuellen Zustand aller Posteingangsdokumente in einer HTML-Übersicht mit 7 Bereichen.

> **ROTE LINIE:** Demo-Ausbaustufe. Keine Produktivfreigabe. Keine neue Fachlogik.

## Liefergegenstände

| Datei | Zweck |
|-------|-------|
| `Config/ui08_posteingang_importstrecke_v1.json` | Konfiguration: 7 Bereiche, Demo-Modus, Sperrregister-Prüfung |
| `Scripts/python_runner/ui08_posteingang_importstrecke.py` | Runner: Liest DuckDB/JSON/CSV, erzeugt HTML/JSON/Bericht |
| `Scripts/python_runner/check_ui08_posteingang_importstrecke.py` | Check-Datei: 20+ systematische Prüfungen |
| `Scripts/UI08_POSTEINGANG_IMPORTSTRECKE_AUTOLAUF.ps1` | PowerShell-Starter: Selbsttest → Hauptlauf → Browser |
| `Projektplanung/UI08_POSTEINGANG_IMPORTSTRECKE.md` | Dokumentation mit Changelog |

## 7 Anzeige-Bereiche

| Bereich | Farbe | Datenquellen |
|---------|-------|--------------|
| Eingang / Intake | Blau | `posteingang_intake`, Entscheidungskarten, Sicherheitskarten |
| Sicherheitsgate | Grün | `posteingang_document_language_profile`, Sicherheitsberichte |
| Sprachkontext | Gelb | `lang_intake_language_rules`, Sprachberichte, Sprachkarten |
| Vorzimmer / Entscheidung | Lila | Vorzimmer-JSON, Entscheidungs-CSV |
| Anwalt / Review | Rot | `anwalt_review_queue`, Anwalt-JSON |
| Agentenbearbeitung | Cyan | `agent_work_queue`, Agent-JSON |
| Schlusskontrolle | Indigo | Schlusskarten, Endabnahme-JSON |

## Abhängigkeiten

UI08 baut auf der bestehenden Posteingang-Infrastruktur auf:

- **Datenbank:** `Database/Legal_Brain.duckdb`
- **Posteingang-Verzeichnis:** `Posteingang/`
- **Bestehende Module:** `005_posteingang_sicherheitsgate_v2`, `012_posteingang_sprachkontext_gate_v2`, `014_posteingang_pipeline_v1`, `016_posteingang_betriebsstatus_v1`, `017_vorzimmer_arbeitsliste_v1`, `018_vorzimmer_entscheidung_v1`, `020_posteingang_gesamtstatus_v1`, `031_dokumentsprachprofil_v1`, `033_posteingang_schlusskontrolle_v2`

## Keine neue Fachlogik

UI08 enthält **keine** neue Geschäftslogik. Es visualisiert nur:
- Welche Daten in der Datenbank vorhanden sind
- Welche JSON-Karten existieren
- Wie viele Dokumente pro Bereich vorhanden sind

## Sperrregister-Prüfung

UI08 prüft das Sperrregister vor dem Start. Bei blockierenden Einträgen wird abgebrochen.

## Startskripte

### PowerShell-Autolauf
```powershell
Scripts\UI08_POSTEINGANG_IMPORTSTRECKE_AUTOLAUF.ps1
```

Ablauf:
1. Selbsttest
2. Hauptlauf (liest alle 7 Bereiche)
3. Posteingang-Übersicht im Browser öffnen

### Python direkt
```bash
python Scripts/python_runner/ui08_posteingang_importstrecke.py
python Scripts/python_runner/ui08_posteingang_importstrecke.py --check
```

## Check-Datei

```bash
python Scripts/python_runner/check_ui08_posteingang_importstrecke.py
```

Prüft:
- Config-Struktur (5 Checks)
- Anzeige-Bereiche (variable Checks)
- Abhängigkeiten (3 Checks)
- Sperrregister (2 Checks)
- Demo-Modus (3 Checks)
- Ausgabe (3 Checks)
- Runner-Struktur (8 Checks)

## Demo-Modus

- Max. 10 Dokumente pro Bereich
- Nur Musterdaten
- Echte Daten **nicht** erlaubt
- Wasserzeichen: "DEMO – UI08 POSTEINGANG ÜBERSICHT"

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstversion: Visuelle Arbeitsübersicht über 7 Posteingangsbereiche, DuckDB/JSON/CSV-Integration, keine neue Fachlogik |
