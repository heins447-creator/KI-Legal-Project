# UI05 – Mandantenakte Gesamtarbeitsplatz / Arbeitszentrale

## Ziel

Zentrale Arbeitsseite, die die bisher getrennten Ansichten UI03 (OCR, Übersetzung, Freigabe, Parkstatus) und UI04b (Sekretariat-Anwalt-Rücklauf, Entscheidung) in einer einzigen Ansicht zusammenführt.

## Anforderungen

1. **Akte öffnen** – Akten-ID anzeigen
2. **Dokumente sehen** – Dokumentenliste aus UI03 + UI04b
3. **OCR-/Übersetzungsstatus sehen** – Status aus UI03-1g
4. **Freigabe-/Parkstatus sehen** – Freigabe- und Parkstatus aus UI03-1g
5. **Sekretariat-/Anwalt-Rücklauf sehen** – Entscheidungsstatus aus UI04b
6. **Nächste zulässige Aktion anzeigen** – Basierend auf Status und Sperrregister
7. **Keine gesperrten Aktionen auslösen** – Sperrregister wird geprüft
8. **Navigationsleiste** – Schnellzugriff auf alle UI-Module (UI05c)
9. **Schaltflächen-Darstellung** – Zulässige Aktionen als Buttons, gesperrte als erklärender Text (UI05c)

## Architektur

### Eingaben (nur lesend)

| Quelle | Datei | Zweck |
|--------|-------|-------|
| UI03-1g | `UI03_1g_GESAMTANSICHT_STATUS.json` | OCR, Übersetzung, Freigabe, Parkstatus |
| UI04b | `UI04b_STATUS.json` | Plausibilität, Dokumente, Fehler, Warnungen |
| UI04b | `UI04b_PLAUSIBILITAET.json` | Detaillierte Plausibilitätsprüfung |
| UI04b | `UI04b_FORMULAR_SCHEMA.json` | Formularstruktur |
| Sperrregister | `sperrregister.json` | Gesperrte Module prüfen |

### Ausgaben

| Datei | Zweck |
|-------|-------|
| `02_Status/UI05_ARBEITSZENTRALE_STATUS.json` | Aggregierter Status |
| `03_Berichte/UI05_BERICHT.txt` | Menschenlesbarer Bericht |
| `05_Fehler/UI05_FEHLER.txt` | Fehler und Warnungen |
| `07_Manifest/UI05_MANIFEST.json` | Datei-Manifest |
| `11_Browseransicht/index.html` | HTML-Ansicht (zentrale Startseite) |

### Ansichtskarten

- **Aktenstatus** – UI03-Status (OCR, Übersetzung, Freigabe, Parkstatus)
- **Entscheidungsstatus** – UI04b-Status (Plausibilität, Dokumente, Fehler, Warnungen)
- **Navigationsleiste** – Schnellzugriff auf alle UI-Module (UI05c)
- **Nächste zulässige Aktionen** – Empfohlene nächste Schritte als Buttons (UI05c)
- **Wartende Aktionen** – Abhängigkeiten (z. B. Übersetzung wartet auf OCR-Freigabe) (UI05b)
- **Gesperrte Aktionen** – Durch Sperrregister blockierte Aktionen (als `action-disabled`, nicht als Button)

## Aktionen-Logik

### Priorisierung (UI05b)

| Priorität | Bedingung | Aktion | Blockierend |
|-----------|-----------|--------|-------------|
| P0 | OCR fehlerhaft | OCR-Fehler prüfen (UI03-1b) | Ja |
| P1 | Freigabe ausstehend | OCR-Freigabe prüfen (UI03-1d) | Nein |
| P2 | Übersetzung ausstehend + OCR frei | Übersetzungsarbeitsplatz öffnen (UI03-1c) | Nein |
| P3 | UI04b fehlerhaft | Entscheidungsmaske korrigieren (UI04b) | Ja |
| P3 | UI04b Warnung | Entscheidung mit Warnungen prüfen (UI04b) | Nein |
| P3 | UI04b OK | Entscheidung freigeben (UI04b) | Nein |
| P4 | Geparkt | Geparkte Aufträge verwalten (UI03-1f) | Nein |

### Gesperrte Aktionen

| Modul | Grund |
|-------|-------|
| `011_quellenbetreuer_fachanwaltsraster_v1` | DB-ändernd + Online-fähig |
| `014_source_adapter_healthcheck_framework_v1` | DB-ändernd + Online-fähig |
| KM21b (Übersetzung) | Fehlende Argos-Sprachpaare |

## Sperrregister-Integration

UI05 liest das [`sperrregister.json`](ALIN_Neustart_Core/01_Register/sperrregister.json) und zeigt gesperrte Aktionen als `action-disabled` (nicht als auslösbaren Button) an. Gesperrte Aktionen können nicht ausgelöst werden.

## Navigation / Bedienbarkeit (UI05c)

- **Navigationsleiste** oben im HTML mit Schnellzugriff auf alle Module
- **Zulässige Aktionen** werden als `<button class="btn-action">` dargestellt (visuell hervorgehoben, nicht klickbar auslösbar, da statisch)
- **Blockierende Aktionen** erhalten zusätzlich die Klasse `blockierend` (rot)
- **Gesperrte Aktionen** werden als `<div class="action-disabled">` dargestellt (grau, opacity 0.7)
- **Abhängigkeiten** (wartende Aktionen) bleiben als gestrichelte Info-Boxen

## Grenzen

- Keine Originaländerung
- Keine neue OCR
- Keine DB-Änderung
- Kein Internet/Cloud
- Keine endgültige Übersetzung behauptet
- Keine Rechtsbewertung
- Keine Beweiswürdigung
- Gesperrte Aktionen nicht auslösen

## Dateien

- `Config/ui05_mandantenakte_arbeitszentrale_v1.json`
- `Scripts/python_runner/ui05_mandantenakte_arbeitszentrale.py`
- `Scripts/python_runner/check_ui05_mandantenakte_arbeitszentrale.py`
- `Scripts/UI05_MANDANTENAKTE_ARBEITSZENTRALE_AUTOLAUF.ps1`
- `Agentensteuerung/UI05_Mandantenakte_Arbeitszentrale/`

## Nächster Auftrag

- UI06: Produktivfreigabe und Deployment-Vorbereitung
- Oder: Weitere UI-Strecken je nach Priorisierung

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| v1 | 2026-05-17 | Erstellerstellung |
| v1.1 (UI05b) | 2026-05-17 | Priorisierung P0-P4, Blockierend-Flag, Abhängigkeiten-Tracking, CSS-Farbmarkierung |
| v1.2 (UI05c) | 2026-05-17 | Navigationsleiste, Buttons für zulässige Aktionen, disabled-Style für gesperrte, Selbsttest erweitert |
