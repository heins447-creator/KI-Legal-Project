# UI07 – Betriebsvorbereitung ohne Produktivfreigabe

## Zweck

UI07 bereitet das System betriebsbereit vor, ohne eine Produktivfreigabe zu erteilen. Es prüft die Start-/Ordnerstruktur, Register, Sperrregister, Healthcheck-Dateien und erzeugt eine Prüfstartseite mit **rotem Rahmen** als sichtbare Warnung.

> **ROTE LINIE:** betriebsbereit vorbereiten, aber **nicht** produktiv setzen.

## Liefergegenstände

| Datei | Zweck |
|-------|-------|
| `Config/ui07_betriebsvorbereitung_v1.json` | Konfiguration: Betriebsmodus, Verzeichnisse, Register-Prüfung, Demo-Modus |
| `Scripts/python_runner/ui07_betriebsvorbereitung.py` | Python-Runner: Prüft Struktur, Register, Sperrregister, erzeugt HTML/JSON/Bericht |
| `Scripts/python_runner/check_ui07_betriebsvorbereitung.py` | Check-Datei: 30+ systematische Prüfungen |
| `Scripts/UI07_BETRIEBSVORBEREITUNG_AUTOLAUF.ps1` | PowerShell-Starter: Selbsttest → Hauptlauf → Browser |
| `Windows_App/Pruefseiten/UI07_Betriebsvorbereitung.html` | Prüfstartseite (bei Ausführung) |
| `Windows_App/Logs/UI07_BETRIEBSSTATUS.json` | Maschinenlesbarer Status (bei Ausführung) |
| `Windows_App/Logs/UI07_BETRIEBSVORBEREITUNG_BERICHT.txt` | Textbericht (bei Ausführung) |

## Betriebsmodus

```json
{
  "betriebsmodus": "vorbereitung",
  "produktiv_freigegeben": false,
  "warnung_roter_rahmen": "DIES IST EINE VORBEREITUNG. KEINE PRODUKTIVFREIGABE. KEINE ECHTEN MANDANTENDATEN."
}
```

## Geprüfte Komponenten

### 1. Verzeichnisstruktur
- `Windows_App/Logs`
- `Windows_App/Daten`
- `Windows_App/Backup`
- `Windows_App/Temp`
- `Windows_App/Pruefseiten`

### 2. Register-Prüfung
- modulregister.json
- sperrregister.json
- toolregister.json
- ressourcenregister.json
- skillregister.json
- lizenzregister.json

### 3. Sperrregister-Prüfung
- Datei vorhanden und valide
- Anzahl Einträge, Kritische, Blockierende
- Kritische Einträge blockieren Start

### 4. Healthcheck
- Register-Dateien
- Schnittstellen-Schemas
- Statusmodelle

### 5. UI-Module
- Prüft, ob Config und Runner für UI03-1b bis UI06 existieren

### 6. Backup-Hinweis
- Letztes Backup-Datum
- Empfohlene Häufigkeit
- Verzeichnis

### 7. Demo-Modus
- Max. 3 Dokumente
- Nur Musterdaten
- Echte Daten **nicht** erlaubt
- Wasserzeichen: "DEMO – KEINE PRODUKTIVFREIGABE"

## Prüfstartseite

Die HTML-Startseite zeigt:
- **Roter Rahmen** mit Warnung
- Betriebsstatus (VORBEREITUNG)
- Verzeichnisstruktur
- Register-Status
- Sperrregister-Übersicht
- Healthcheck-Ergebnisse
- UI-Module-Grid
- Backup-Hinweis
- Demo-Modus-Einschränkungen

## Startskripte

### PowerShell-Autolauf
```powershell
Scripts\UI07_BETRIEBSVORBEREITUNG_AUTOLAUF.ps1
```

Ablauf:
1. Verzeichnisse sicherstellen
2. Python-Prüfung
3. Config- und Runner-Prüfung
4. Selbsttest
5. Hauptlauf
6. Prüfstartseite im Browser öffnen

### Python direkt
```bash
python Scripts/python_runner/ui07_betriebsvorbereitung.py
python Scripts/python_runner/ui07_betriebsvorbereitung.py --check  # Selbsttest
```

## Check-Datei

```bash
python Scripts/python_runner/check_ui07_betriebsvorbereitung.py
```

Prüft:
- Config-Struktur (11 Checks)
- Verzeichnisse (5 Checks)
- Register (7 Checks)
- Sperrregister (3 Checks)
- Healthcheck (3 Checks)
- Demo-Modus (4 Checks)
- Backup (2 Checks)
- Startseite (3 Checks)
- Ausgabe (3 Checks)
- Python-Runner (10 Checks)
- Grenzen (3 Checks)

## Keine Produktivfreigabe

UI07 ist explizit **keine** Produktivfreigabe. Die rote Linie:

- `produktiv_freigegeben: false`
- `echte_daten_erlaubt: false`
- `nur_musterdaten: true`
- Roter Rahmen auf der Prüfstartseite
- Wasserzeichen auf allen Ausgaben

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2026-05-17 | Erstversion: Betriebsvorbereitung mit Prüfstartseite, rotem Rahmen, Sperrregister-Prüfung, Demo-Modus |
