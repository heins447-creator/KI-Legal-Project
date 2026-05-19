# CORE-25: Programmierbare Gesamt-Roadmap

## Ziel

Das fachliche Gesamtkonzept der lokalen Kanzleisoftware wird in eine maschinenlesbare Roadmap fuer CORE-24 (Autonomer Entwicklungsmanager) zerlegt.

Die Roadmap enthaelt pro Modul/Stufe:
- **Stufen-Nummer und Name**
- **Abhaengigkeiten** (welche Module muessen vorher fertig sein)
- **Eingaben** (Dateien, Daten, Configs die benoetigt werden)
- **Ausgaben** (Dateien, Berichte, Manifeste die erzeugt werden)
- **Sperren** (was blockiert dieses Modul)
- **Tests** (welche Pruefungen muessen bestanden werden)
- **Erlaubte naechste Module** (was kann danach kommen)
- **Blockierte Module** (was darf danach noch nicht kommen)
- **Prioritaet** (Reihenfolge)
- **Fertigstellungskriterien** (Definition of Done)

## Lieferpflichten

Aus AGENTS.md:
1. Python-Laeufer unter `Scripts/python_runner/`
2. Pruefdatei unter `Scripts/python_runner/`
3. PowerShell-Starter unter `Scripts/`
4. Konfiguration unter `Config/`
5. Dokumentation unter `Projektplanung/`
6. Testlauf
7. Bericht unter `ALIN_Neustart_Core/Reports/`
8. Git-Status vor und nach Aenderung
9. Git-Commit nur bei erfolgreichem Build und erfolgreicher Pruefung

## Erzeugte Dateien

| Datei | Pfad |
|-------|------|
| Python-Runner | `Scripts/python_runner/core25_gesamt_roadmap.py` |
| Check-Datei | `Scripts/python_runner/check_core25_gesamt_roadmap.py` |
| PowerShell-Starter | `Scripts/CORE25_GESAMT_ROADMAP_AUTOLAUF.ps1` |
| Konfiguration | `Config/core25_roadmap_v1.json` |
| Dokumentation | `Projektplanung/CORE25_GESAMT_ROADMAP.md` |
| Ergebnis JSON | `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE25_gesamt_roadmap.json` |
| Bericht | `ALIN_Neustart_Core/Reports/CORE25_GESAMT_ROADMAP_BERICHT.txt` |

## Datenquellen

- `ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md`
- `ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md`
- `ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md`
- `ALIN_Neustart_Core/00_Dokumentation/ALIN_NAECHSTE_AUFTRAEGE.md`
- `Config/core24_entwicklungsmanager_v1.json`
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE24_auftragsqueue.json`

## Phasen der Roadmap

### Phase 0: Vorbereitung
- **CORE-00**: Masterauftrag und Grundmodell

### Phase 1: Grundmodell vervollstaendigen (CORE-01 bis CORE-05)
- **CORE-01**: Register befuellen
- **CORE-02**: Statusmodell implementieren
- **CORE-03**: Schnittstellenvertraege finalisieren
- **CORE-04**: Healthcheck implementieren
- **CORE-05**: Resolver implementieren

### Phase 2: Altbestand anbinden (CORE-06 bis CORE-10)
- **CORE-06**: Altbestand inventarisieren
- **CORE-07**: Posteingang anbinden
- **CORE-08**: OCR-Strecke anbinden
- **CORE-09**: UI anbinden
- **CORE-10**: Quellen und Skills anbinden
- **CORE-10a bis CORE-10g**: Detail-Teilschritte

### Phase 3: Windows-App-Grundlage (CORE-11 bis CORE-15)
- **CORE-11**: Windows-App-Architektur finalisieren
- **CORE-12**: UI-Grundlagen implementieren
- **CORE-13**: Altbestand inventarisiert und inventur
- **CORE-14**: CORE13-Auswertung und Sperrplan
- **CORE-15**: Migrationsplan und kopierende Migration

### Phase 4: Test und Abnahme (CORE-16 bis CORE-20)
- **CORE-16**: Neustruktur-Validierung und Reste-Archiv
- **CORE-17**: Arbeitsindex und Agenten-Einstieg
- **CORE-18**: Projekt-Dashboard
- **CORE-19**: Rechte und Rollen
- **CORE-20**: Datenschutz und Mandatsgeheimnis

### Phase 5: Autonomer Betrieb (CORE-21 bis CORE-25)
- **CORE-21**: Arbeitsindex und Agentenregeln
- **CORE-22**: Agenten-Einstieg
- **CORE-23**: Projekt-Dashboard
- **CORE-24**: Autonomer Entwicklungsmanager
- **CORE-25**: Programmierbare Gesamt-Roadmap

### UI-Strecke (UI01 bis UI14)
- UI01 Anwaltsansicht -> UI02 Tuerschwelle -> UI02c Freigabe -> UI03_0 Uebergabe -> UI03_1 Dreiansicht -> UI03_1b OCR-Kontrolle -> UI03_1c Uebersetzungsarbeitsplatz -> UI03_1d OCR-Freigabe -> UI03_1e Uebergabe-Freigabe -> UI03_1f Geparkte Auftraege -> UI03_1g Gesamtansicht -> UI04 Durchstich -> UI04b Logikpruefung -> UI05 Mandantenakte -> UI06 Musterlauf -> UI06b Fehlerpfad -> UI07 Betriebsvorbereitung -> UI07b Gesamtfreeze -> UI08 Posteingang -> UI08b Fehlerpfad-Posteingang -> UI08c Sanierungsplan -> UI09 Zentrale -> UI10 Profil-LES-Adapter -> UI11 Register-LES-Adapter -> UI12 Master-Adapter -> UI13 Abnahme -> UI14 Nachlaufzentrale

### OCR- und Uebersetzungsstrecke (KM12 bis KM21)
- KM12 Originalabbildung -> KM12b Uebergrosse Abbildungen -> KM13 OCR-Pipeline -> KM13b Tesseract-Sprachpaket -> KM14 Maschinenformat -> KM15 Arbeitsuebersetzung -> KM16 Sprachrouting -> KM17 OCR-Integration -> KM17c Einzelseite -> KM18 Ergebnisdiagnose -> KM19 Gesamtkette -> KM19b OCRBetreuer -> KM20 Konsolidierung -> KM20b Bereinigung -> KM21 Translation-Env -> KM21b0 ARGOS

### Posteingang und Vorzimmer
- POST01 Intake -> POST02 Schlusskontrolle -> POST03 Endabnahme -> VZ01 Kommunikationsparameter

### Quellen und Agenten
- Q01 Quellenbetreuer -> Q02 Quellenkandidaten -> Q03 Source-Adapter-Healthcheck
- AG01 Agentenbearbeitung -> AG02 Dokumentart -> AG03 Sprache -> AG04 Sachverhaltsbezug

### Build und Release
- WINAPP: Windows App Build
- DEPLOY: Deployment und Betrieb

### Abschluss
- CORE-26: Gesamtabnahme und Produktionsfreigabe (gesperrt - menschliche Freigabe erforderlich)

## Format-Kompatibilitaet

Die Roadmap-JSON ist fuer CORE-24 lesbar:
- Meta-Block mit `modul_id`, `name`, `version`, `zeitstempel_erstellung`
- `roadmap.stufen[]` als Array
- Jede Stufe hat `stufe_id`, `name`, `abhaengigkeiten[]`, `eingaben[]`, `ausgaben[]`, `tests[]`, `prioritaet`, `status`, `fertigstellungskriterien[]`
- `validierung` Block mit Zyklenfreiheit, Eindeutigkeit, Aufloesbarkeit

## Regeln

- Nur Befehle aus `AGENTENFREIGABE_KLARSTELLUNG.txt` verwenden
- Keine destruktiven Operationen
- Roadmap muss von CORE-24 lesbar sein (kompatibles JSON-Format)
- Abhaengigkeiten muessen zyklenfrei sein
- Jedes Modul braucht eindeutige ID, Status, Prioritaet
- Git-Commit nur bei erfolgreichem Build und erfolgreicher Pruefung

## Autor
CORE-25 Autonomer Agent / KI_Legal_Project
