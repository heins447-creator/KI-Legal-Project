# UI07b – Gesamtfreeze Demo-Betriebsstrecke ohne Produktivfreigabe

## Zweck

UI07b friert die gesamte UI03–UI07-Demo-Betriebsstrecke ein. Es prüft, ob alle erwarteten Dateien existieren und committed sind, und erzeugt eine Gesamt-Übersicht. **Keine neue Fachlogik.**

> **ROTE LINIE:** Demo-Betriebsstrecke eingefroren. Keine Änderungen ohne expliziten Auftrag.

## Liefergegenstände

| Datei | Zweck |
|-------|-------|
| `Config/ui07b_gesamtfreeze_demo_betriebsstrecke_v1.json` | Konfiguration: Modul-Liste, erwartete Dateien, Freeze-Regeln |
| `Scripts/python_runner/ui07b_gesamtfreeze_demo_betriebsstrecke.py` | Runner: Prüft Existenz + Git-Status aller UI03–UI07-Dateien, erzeugt HTML/JSON/Bericht |
| `Scripts/python_runner/check_ui07b_gesamtfreeze_demo_betriebsstrecke.py` | Check-Datei: 25+ systematische Prüfungen |
| `Scripts/UI07B_GESAMTFREEZE_DEMO_BETRIEBSSTRECKE_AUTOLAUF.ps1` | PowerShell-Starter: Selbsttest → Hauptlauf → Browser |
| `Projektplanung/UI07B_GESAMTFREEZE_DEMO_BETRIEBSSTRECKE.md` | Dokumentation mit Changelog |

## Eingefrorene Strecke

| Modul | Name | Status |
|-------|------|--------|
| UI03-1b | OCR-/Übersetzungskontrolle | Eingefroren |
| UI03-1c | Übersetzungsarbeitsplatz | Eingefroren |
| UI03-1d | OCR-Freigabeablauf | Eingefroren |
| UI03-1e | Übergabe Freigabeentscheidung | Eingefroren |
| UI03-1f | Geparkte Aufträge verwalten | Eingefroren |
| UI03-1g | Kombinierte Gesamtansicht | Eingefroren |
| UI04b | Logikprüfung und Entscheidung | Eingefroren |
| UI05 | Mandantenakte Arbeitszentrale | Eingefroren |
| UI06 | Musterlauf Gesamtkette | Eingefroren |
| UI06b | Fehlerpfadprüfung Gesamtkette | Eingefroren |
| UI07 | Betriebsvorbereitung | Eingefroren |

## Freeze-Regeln

1. Keine Änderungen an UI03–UI07-Modulen ohne expliziten Auftrag.
2. Keine neue Fachlogik in der Demo-Betriebsstrecke.
3. Erlaubt: Bugfixes, Textkorrekturen, Dokumentationsupdates.
4. Erlaubt: Neue Module außerhalb der Demo-Strecke (UI08+).
5. Jede Änderung erfordert neuen Freeze-Check (UI07b wiederholen).

## Geprüfte Dateien pro Modul

Jedes Modul wird auf folgende Dateien geprüft:
- **Config** (`Config/ui*.json`)
- **Runner** (`Scripts/python_runner/ui*.py`)
- **Check** (`Scripts/python_runner/check_ui*.py`)
- **Starter** (`Scripts/UI*_AUTOLAUF.ps1`)
- **Doku** (`Projektplanung/UI*.md`)

Zusätzlich werden ergänzende Dateien geprüft:
- UI03-0 Übergabe Mandantenakte
- UI01 Anwaltsansicht
- UI04 Durchstich Sekretariat-Anwalt-Rücklauf

## Git-Status-Prüfung

Jede Datei wird auf Git-Status geprüft:
- **Committed** → OK
- **Untracked / Modified** → Warnung
- **Fehlt** → Fehler

## Freeze-Übersicht (HTML)

Die erzeugte HTML-Seite zeigt:
- Roter Freeze-Banner
- Freeze-Status und -Datum
- Modul-Grid mit OK/Warnung/Fehler
- Detaillierte Dateiliste pro Modul
- Git-Status jeder Datei
- Ergänzende Dateien

## Startskripte

### PowerShell-Autolauf
```powershell
Scripts\UI07B_GESAMTFREEZE_DEMO_BETRIEBSSTRECKE_AUTOLAUF.ps1
```

Ablauf:
1. Selbsttest
2. Hauptlauf (prüft alle 11 Module)
3. Freeze-Übersicht im Browser öffnen

### Python direkt
```bash
python Scripts/python_runner/ui07b_gesamtfreeze_demo_betriebsstrecke.py
python Scripts/python_runner/ui07b_gesamtfreeze_demo_betriebsstrecke.py --check
```

## Check-Datei

```bash
python Scripts/python_runner/check_ui07b_gesamtfreeze_demo_betriebsstrecke.py
```

Prüft:
- Config-Struktur (7 Checks)
- Modul-Liste (11 Checks)
- Dateipfade pro Modul (variable Checks)
- Ergänzende Dateien (variable Checks)
- Freeze-Regeln (3 Checks)
- Ausgabe (3 Checks)
- Runner-Struktur (10 Checks)

## Keine neue Fachlogik

UI07b enthält **keine** neue Geschäftslogik. Es ist ein reines Review- und Freeze-Modul, das die bestehende Strecke zusammenfasst und validiert.

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstversion: Freeze der UI03–UI07-Demo-Betriebsstrecke, Git-Status-Prüfung, Gesamt-Übersicht |
