# CORE-03 – Registerqualität prüfen, Lücken klassifizieren und Nachinventarisierung planen

**Datum:** 2026-05-16  
**Analyst:** ALIN Core-Agent  
**Scope:** ALIN_Neustart_Core/01_Register/ und 07_Bestandsaufnahme_Altbestand/  
**Methodik:** Lesende Analyse der CORE-02 Inventardaten, Schema-Validierung, Plausibilitätsprüfung gegen Altbestand

---

## 1. Zusammenfassung der Inventurlage (CORE-02)

| Register | Einträge | Schema-Validierung | Status |
|----------|----------|-------------------|--------|
| Modulregister | 163 | OK | Produktiv |
| Ressourcenregister | 2 | OK | Lückenhaft |
| Toolregister | 3 | OK | Lückenhaft |
| Skillregister | 5 | OK | Unvollständig |
| Quellen-/Adapter-Register | 1 | OK | Lückenhaft |
| Lizenzregister | 1 | OK | Lückenhaft |
| Update-Register | 0 | OK (leer) | Leer |

---

## 2. Modulregister – Kategorisierungsprüfung

### 2.1 Verteilung nach Dateityp (163 Module)

| Kategorie | Anzahl | Anteil | Bewertung |
|-----------|--------|--------|-----------|
| PowerShell-Skripte (.ps1) | ~45 | 28% | OK – Starter und Autoläufe |
| Python-Skripte (.py) | ~105 | 64% | OK – Runners, Agents, Checks |
| SQL-Migrationen (.sql) | ~11 | 7% | OK – Datenbankschema |
| C#-Quellcode (.cs) | ~2 | 1% | OK – Windows-App |

**Bewertung:** Die Kategorisierung ist korrekt. Die Verteilung spiegelt die Architektur wider:
- Python als Hauptarbeitsprache für Datenverarbeitung
- PowerShell als Infrastruktur- und Startsprache
- SQL für Datenbankmigrationen
- C# für die Windows-App-Oberfläche

### 2.2 Qualitätsdefizite im Modulregister

| Defizit | Anzahl (geschätzt) | Schwere |
|---------|-------------------|---------|
| Keine Beschreibung (zweck = "Keine Beschreibung verfuegbar") | ~90% | Mittel |
| Version = "unbekannt" | ~95% | Niedrig |
| Keine Abhängigkeiten (abhaengig_von = ["unbekannt"]) | ~98% | Hoch |
| Keine Ein-/Ausgabe-Schemas verknüpft | 100% | Hoch |

**Kritisch:** Die Abhängigkeitskette ist nicht verzeichnet. Bei 163 Modulen ohne dokumentierte Abhängigkeiten besteht das Risiko von Kaskadenfehlern bei Änderungen.

### 2.3 Kategorisierungsfehler

Keine offensichtlichen Fehler gefunden. Die Zuordnung nach Dateityp ist technisch korrekt.  
**Verbesserungspotenzial:** Eine semantische Kategorisierung (z. B. "Posteingang", "OCR", "UI", "Agent") wäre hilfreicher als die reine Dateityp-Klassifikation.

---

## 3. Warum so wenige Einträge in den anderen Registern?

### 3.1 Ressourcenregister – Nur 2 Einträge

**Erfasst:**
- `TESS_DEU` (Tesseract OCR Deutsch)
- `TESS_SWE` (Tesseract OCR Schwedisch)

**Fehlend (mindestens):**
- Weitere Tesseract-Sprachpakete (en, fr, es, it, pl, …)
- Übersetzungsmodelle (z. B. für KM15/KM21)
- Terminologien (Rechtsfachwörterbücher)
- Schriftarten (für OCR-Optimierung)
- Windows-App-Ressourcen (XAML, Bilder)

**Ursache:** Die CORE-02-Extraktionslogik (`alin_core02_altbestand_inventar.py`) prüft nur auf EXE-Dateien im Scripts/-Verzeichnis. Ressourcen (Sprachpakete, Modelle, Schriftarten) sind verteilt im Dateisystem und wurden nicht gescannt.

### 3.2 Toolregister – Nur 3 Einträge

**Erfasst:**
- `AIDER` (AI Coding Agent)
- `PYTHON` (Python-Interpreter)
- `TESSERACT` (Tesseract OCR)

**Fehlend (mindestens):**
- Git-Client
- PowerShell-Engine (Systemkomponente, aber relevant für Offline-Betrieb)
- .NET-Runtime (für Windows-App)
- WebView2-Runtime (für UI)
- Datenbank-Engine (SQLite oder andere)
- PDF-Tools (z. B. für Originalabbildung)
- Alle Tools aus `ALIN_Neustart_Core/09_Toolbibliothek/`

**Ursache:** Gleiche wie bei Ressourcen – nur EXE-Dateien in Scripts/ wurden berücksichtigt. Die Toolbibliothek (`09_Toolbibliothek/`) wurde nicht inventarisiert.

### 3.3 Skillregister – 5 Einträge

**Erfasst:**
- `SKILL_OCR` (OCR-Pipeline)
- `SKILL_DOKUMENTART` (Dokumentart erkennen)
- `SKILL_SACHVERHALTSBEZUG` (Sachverhaltsbezug herstellen)
- `SKILL_SPRACHE` (Sprache erkennen/übersetzen)
- `SKILL_QUELLEN` (Quellenbetreuung)

**Bewertung:** Die 5 Skills wurden aus speziellen Python-Runnern extrahiert, die explizit als "Skill" markiert sind.  
**Fehlend:**
- Implizite Skills (z. B. "Posteingang verarbeiten", "Vorzimmer entscheiden", "Anwaltsansicht rendern")
- UI-Skills (Dropdown-Freigabe, Dreiansicht, Durchstich)
- Metaskills (Orchestrierung, Qualitätskontrolle)

**Ursache:** Skills werden nicht automatisch erkannt. Nur Module mit expliziter "Skill"-Bezeichnung im Namen oder Docstring wurden erfasst.

### 3.4 Quellen-/Adapter-Register – Nur 1 Eintrag

**Erfasst:**
- `EUR_LEX` (Eur-Lex, aus `051_quellenkandidaten_eu_se_v1.py`)

**Fehlend (mindestens):**
- Alle Quellen aus `Projektplanung/Quellen/`
- Datenbank-Quellen (Migrationsdateien)
- Offline-Cache-Quellen
- Gerichtsentscheidungsdatenbanken

**Ursache:** Nur der EU-Quellenkandidaten-Runner wurde als Quellenquelle erkannt. Die eigentlichen Quellen-Dokumentationen und Adapter-Implementierungen wurden nicht gescannt.

### 3.5 Lizenzregister – Nur 1 Eintrag

**Erfasst:**
- `TESSERACT` (Apache-2.0)

**Fehlend:**
- Python-Lizenz (PSF)
- Aider-Lizenz
- Git-Lizenz
- Alle Third-Party-Python-Packages
- Windows-App-Abhängigkeiten (.NET, WebView2)
- Tesseract-Sprachpaket-Lizenzen

**Ursache:** Lizenzinformationen sind nicht strukturiert im Code verfügbar. Sie müssen manuell recherchiert oder aus Lizenzdateien extrahiert werden.

### 3.6 Update-Register – 0 Einträge

**Fehlend:**
- Tesseract-Version-Updates
- Python-Version-Updates
- Sprachpaket-Updates
- Schema-Migration-Updates
- Tool-Updates aus `09_Toolbibliothek/`

**Ursache:** Es gibt keine Extraktionslogik für Updates. Das Update-Register ist konzeptionell vorgesehen (siehe `10_Update_Ueberwachung/`), aber die automatische Inventarisierung hat keine Update-Informationen gefunden.

---

## 4. Lückenanalyse (aus `altbestand_luecken.json`)

### 4.1 Bestandslücken nach Kategorie

| Kategorie | Anzahl | Schwere | Priorität |
|-----------|--------|---------|-----------|
| Ressourcen | ~8 | Hoch | Dringend |
| Tools | ~6 | Hoch | Dringend |
| Module | ~3 | Mittel | Hoch |
| Register | ~2 | Mittel | Hoch |
| Schnittstellen | ~1 | Niedrig | Mittel |

### 4.2 Lücken nach Schweregrad

| Schwere | Anzahl | Beispiele |
|---------|--------|-----------|
| Blockierend | 0 | (Keine) |
| Hoch | ~12 | Update-Register leer, Toolregister unvollständig, fehlende Abhängigkeiten |
| Mittel | ~5 | Unvollständige Beschreibungen, fehlende Versionsangaben |
| Niedrig | ~2 | Semantische Kategorisierung, Windows-App-Ressourcen |

### 4.3 Lücken nach Priorität (bereits klassifiziert in `altbestand_luecken.json`)

| Priorität | Anzahl | Typische Lücken |
|-----------|--------|------------------|
| Dringend | ~5 | Update-Register, Toolregister, Ressourcenregister |
| Hoch | ~8 | Abhängigkeiten, Quellen-Adapter, Lizenzregister |
| Mittel | ~4 | Beschreibungen, Skills, Schnittstellen |
| Niedrig | ~2 | C#-Windows-App-Module, Metadaten |

---

## 5. Nachinventarisierungsaufträge (formuliert)

### P0 – DRINGEND (Blockiert weitere CORE-Aufträge)

| Auftrag | Ziel | Umfang |
|---------|------|--------|
| **CORE-03a** | Update-Register befüllen | Scan `10_Update_Ueberwachung/`, Tool-Versionen prüfen, Sprachpaket-Versionsstände ermitteln |
| **CORE-03b** | Toolregister vervollständigen | Scan `09_Toolbibliothek/`, System-Runtimes identifizieren (PowerShell, .NET, WebView2, Git) |
| **CORE-03c** | Ressourcenregister vervollständigen | Alle Tesseract-Sprachpakete verzeichnen, Übersetzungsmodelle, Schriftarten, Terminologien |

### P1 – HOCH (Erforderlich für Gesamtkonsistenz)

| Auftrag | Ziel | Umfang |
|---------|------|--------|
| **CORE-03d** | Quellen-/Adapter-Register vervollständigen | Alle Quellen aus `Projektplanung/Quellen/` und `Database/Migrations/` inventarisieren, Adapter-Zuordnung prüfen |
| **CORE-03e** | Modul-Beschreibungen nachtragen | SYNOPSIS/DESCRIPTION aus PowerShell-Docstrings, Python-Docstrings, SQL-Kommentaren extrahieren |
| **CORE-03f** | Modul-Versionen prüfen | Versionsangaben aus Dateinamen (`_v1.py`) oder Metadaten extrahieren, SemVer konform verzeichnen |

### P2 – MITTEL (Qualitätsverbesserung)

| Auftrag | Ziel | Umfang |
|---------|------|--------|
| **CORE-03g** | Modul-Abhängigkeiten vervollständigen | `import`-Statements in Python, `Requires` in PowerShell, Foreign Keys in SQL analysieren |
| **CORE-03h** | Skillregister vervollständigen | Implizite Skills aus Workflow-Dokumentationen (`Projektplanung/`) identifizieren, UI-Skills ergänzen |
| **CORE-03i** | Lizenzregister vervollständigen | Third-Party-Lizenzen aus `09_Toolbibliothek/05_Lizenzen/`, Python-Package-Lizenzen, .NET-Abhängigkeiten |

### P3 – NIEDRIG (Optional/Komfort)

| Auftrag | Ziel | Umfang |
|---------|------|--------|
| **CORE-03j** | Altbestand-Modulkarte mit Windows-App-Modulen ergänzen | `Windows_App/App/*.cs` und `*.xaml` in `altbestand_modulkarte.json` ergänzen |
| **CORE-03k** | Schnittstellen-Dokumentation vervollständigen | Eingabe-/Ausgabe-Schemas in `03_Schnittstellen/` mit Modulregister verknüpfen |
| **CORE-03l** | Semantische Modulkategorisierung | Module nach Geschäftsprozess (Posteingang, OCR, Übersetzung, UI, Agent) statt Dateityp klassifizieren |

---

## 6. Empfohlene Reihenfolge

```
P0: CORE-03a → CORE-03b → CORE-03c
         ↓
P1: CORE-03d → CORE-03e → CORE-03f
         ↓
P2: CORE-03g → CORE-03h → CORE-03i
         ↓
P3: CORE-03j → CORE-03k → CORE-03l
```

**Begründung:**
- Update-Register (P0) ist Voraussetzung für den Healthcheck
- Tool- und Ressourcenregister (P0) sind Voraussetzung für Offline-Betrieb
- Abhängigkeiten (P2) setzen vollständige Modulbeschreibungen (P1) voraus

---

## 7. Risiken

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|-------------------|------------|------------|
| Manuelle Nachinventarisierung ist fehleranfällig | Hoch | Inkonsistenzen | Prüfscripte (wie `alin_core02_pruefung.py`) für jeden Auftrag erstellen |
| Versionsangaben in Dateinamen sind unzuverlässig | Mittel | Falsche Versionen | Hash-basierte Identifikation ergänzen |
| Abhängigkeiten ändern sich laufend | Hoch | Veraltete Register | Regelmäßige Re-Inventarisierung (CORE-04) planen |

---

## 8. Fazit

Die CORE-02-Inventarisierung hat 163 Module korrekt erfasst und kategorisiert.  
**Kritisch fehlend:** Update-Register (0 Einträge), unvollständige Tool-/Ressourcenregister, fehlende Abhängigkeitsdokumentation.  
**Empfohlung:** P0-Aufträge als nächstes bearbeiten, da sie die Grundlage für Healthchecks, Offline-Betrieb und weitere CORE-Module bilden.

---

*Dokumentation erstellt im Rahmen von CORE-03.*  
*Liegt unter: ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/CORE03_Registerqualitaet_Luecken_Nachinventarisierung.md*
