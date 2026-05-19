# CORE-21: Umschalt- und Arbeitsindex

## Ziel

Nach erfolgreicher Migration CORE-14 bis CORE-20 (311 Dateien kopiert, 98.125 restliche Dateien klassifiziert) wird ein klarer Einstiegspunkt geschaffen, der definiert:

1. Welche der 311 kopierten Dateien gelten als neuer Arbeitsbestand
2. Welche Skripte sind künftig maßgeblich
3. Welche Altdateien dürfen nicht mehr direkt benutzt werden
4. Welche Restgruppen bleiben gesperrt, manuell zu prüfen oder Archivvorschlag
5. Welche Startdatei oder Übersicht benutzt Roo künftig zuerst
6. Welche alten Pfade sind nur noch Referenz, nicht mehr Arbeitsgrundlage

## Liefergegenstände

| Datei | Pfad | Zweck |
|-------|------|-------|
| Python-Runner | `Scripts/python_runner/core21_arbeitsindex.py` | Erstellt Arbeitsindex und Bericht |
| Check-Datei | `Scripts/python_runner/check_core21_arbeitsindex.py` | Prüft alle Ausgaben |
| PowerShell-Starter | `Scripts/CORE21_ARBEITSINDEX_AUTOLAUF.ps1` | Automatischer Ablauf |
| Konfiguration | `Config/core21_arbeitsindex_v1.json` | Arbeitsmodus-Konfiguration |
| Arbeitsindex | `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_arbeitsindex.json` | Maschinenlesbare Indexdatei |
| Bericht | `ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt` | Menschenlesbarer Bericht |

## Eingabedaten

- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE17_kopierte_dateien_manifest.json` (311 Einträge)
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE19_reste_archiv_sperrplan.json`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE14_auswertung.csv`
- `ALIN_Neustart_Core/Reports/CORE20_MASTER_UMBAU_BERICHT.txt`

## Struktur des Arbeitsindex

### 1. Arbeitsbestand

Liste der 311 Dateien, die aktiv bearbeitet werden:
- Dokumentation (ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md, ALIN_MODULPAKETE.md, etc.)
- Register (modulregister.json, quellen_adapter_register.json, etc.)
- Schemata & Statusmodelle (statusmodell.schema.json, akte_status.json, etc.)
- Schnittstellen & Resolver
- Healthcheck & Audit
- Konfigurationsprofile
- Teststrategie & Architekturentscheidungen

### 2. Referenzbestand

Liste der 311 Dateien im Migrationsverzeichnis:
- Kopien aus CORE-17 unter `08_Migration/02_Kopierte_Dateien/`
- Nur Referenz, keine aktive Bearbeitung

### 3. Gesperrte Pfade

Restgruppen aus CORE-19:
| Status | Anzahl | Maßnahme |
|--------|--------|----------|
| gesperrt | 6.492 | Nicht kopieren, nicht bearbeiten |
| manuell | 25.385 | Manuell prüfen |
| archiv | 1.643 | Archivvorschlag |
| dublette | 59.879 | Dubletten, nicht kopieren |
| testrest | 3.359 | Testreste, nicht kopieren |
| laufzeit | 1.367 | Laufzeitartefakte, nicht kopieren |

### 4. Empfohlener Start für Roo

**Primär:** `ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md`

**Alternativen:**
- `ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md`
- `ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md`
- `ALIN_Neustart_Core/00_Dokumentation/ALIN_PROFESSIONELLE_SOFTWARE_KONSTRUKTION.md`

### 5. Alte Arbeitsbereiche (nicht mehr aktiv)

- `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/`
- `ALIN_Neustart_Core/08_Migration/02_Kopierte_Dateien/`
- `ALIN_Neustart_Core/08_Migration/09_Manifest/`
- `Agentensteuerung/`
- `07_Berichte/`
- `10_Tool_Inventar/`

### 6. Neue Arbeitsbereiche (zukünftige Arbeit)

- `ALIN_Neustart_Core/00_Dokumentation/` – Dokumentation und Masteraufträge
- `ALIN_Neustart_Core/01_Register/` – Tool-, Quellen-, Ressourcen-Register
- `ALIN_Neustart_Core/02_Statusmodell/` – Statusmodelle
- `ALIN_Neustart_Core/03_Schnittstellen/` – Übergabeschemata
- `ALIN_Neustart_Core/04_Healthcheck/` – Healthcheck-Regeln und Status
- `ALIN_Neustart_Core/05_Resolver/` – Resolver-Schemata
- `ALIN_Neustart_Core/06_Audit_Protokoll/` – Protokoll-Schemata
- `ALIN_Neustart_Core/10_Update_Ueberwachung/` – Update-Register und Monitoring
- `ALIN_Neustart_Core/12_Dokumentation_Hilfe_Infofelder/` – UI-Texte und Hilfe
- `ALIN_Neustart_Core/13_Anforderungen_Abnahme/` – Abnahmekriterien
- `ALIN_Neustart_Core/14_Architekturentscheidungen/` – ADRs
- `ALIN_Neustart_Core/15_Teststrategie/` – Testpläne und Kataloge
- `ALIN_Neustart_Core/23_Import_Export/` – Portabilitätsregeln
- `ALIN_Neustart_Core/24_Konfigurationsprofile/` – Konfigurationsprofile
- `Projektplanung/` – Projektplanungsdokumente
- `Scripts/python_runner/` – Python-Runner
- `Config/` – Konfigurationsdateien
- `Database/Migrations/` – Datenbankmigrationen
- `Windows_App/` – Windows-Anwendung

## Skript-Priorität

1. `Scripts/python_runner/` – Aktive Python-Läufer
2. `ALIN_Neustart_Core/Scripts/` – Core-Skripte
3. `Scripts/` – Allgemeine PowerShell-Starter

## Ausführung

```powershell
.\Scripts\CORE21_ARBEITSINDEX_AUTOLAUF.ps1
```

Der Autolauf führt aus:
1. `py_compile` auf Runner und Checker
2. Ausführung von `core21_arbeitsindex.py`
3. Ausführung von `check_core21_arbeitsindex.py`
4. Zusammenfassung der Ergebnisse

## Abhängigkeiten

- CORE-14 (Auswertung)
- CORE-15 (Migrationsplan)
- CORE-16 (Dry-Run)
- CORE-17 (Kopierende Migration)
- CORE-18 (Neustruktur-Validierung)
- CORE-19 (Reste-/Archiv-/Sperrplan)
- CORE-20 (Master-Umbau-Bericht)

## Version

- CORE-21 v1.0.0
- Zeitstempel: 2026-05-18
