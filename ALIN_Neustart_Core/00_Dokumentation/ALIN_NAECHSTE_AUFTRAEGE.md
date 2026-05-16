# ALIN Nächste Aufträge

## Phase 1: Grundmodell vervollständigen (CORE-01 bis CORE-05)

### CORE-01: Register befüllen
- Modulregister mit Altbestand abgleichen
- Ressourcenregister mit vorhandenen Sprachpaketen, OCR-Modellen, Übersetzungsressourcen befüllen
- Skillregister mit vorhandenen Agenten/Skills befüllen
- Quellen-/Adapterregister mit vorhandenen Quellen befüllen
- Toolregister mit vorhandenen Tools befüllen
- Lizenzregister mit vorhandenen Komponenten befüllen
- Update-Register initialisieren

### CORE-02: Statusmodell implementieren
- Status-JSON-Dateien mit Übergangsregeln
- Fehlerklassen definieren
- Status-Validierung

### CORE-03: Schnittstellenverträge finalisieren
- Alle Übergabe-Schemas prüfen und abstimmen
- Pflichtfelder validieren
- Beispiel-Objekte erstellen

### CORE-04: Healthcheck implementieren
- Systemstart-Healthcheck als Python-Runner
- Prüfung aller Bestandteile
- Berichtserstellung

### CORE-05: Resolver implementieren
- Aktenprofil-Resolver
- Ressourcen-Resolver
- Workflow-Resolver
- Tool-Resolver
- Quellen-Resolver

## Phase 2: Altbestand anbinden (CORE-06 bis CORE-10)

### CORE-06: Altbestand inventarisieren
- Modulkarte erstellen
- Ressourcenkarte erstellen
- Schnittstellenkarte erstlegen
- Lücken identifizieren
- Toolkarte erstellen
- Lizenzhinweise sammeln

### CORE-07: Posteingang anbinden
- Posteingang als Modul im Modulregister eintragen
- Schnittstelle Posteingang → Sekretariat definieren
- Statusübergänge abbilden

### CORE-08: OCR-Strecke anbinden
- KM12–KM21 als Modulpaket eintragen
- Schnittstelle Weiche → OCR definieren
- Schnittstelle OCR → Akte definieren

### CORE-09: UI anbinden
- UI01–UI04 als Modulpaket eintragen
- Schnittstelle Weiche → Anwalt definieren
- Schnittstelle Rücklauf definieren

### CORE-10: Quellen und Skills anbinden
- Quellenbetreuer, Agenten, Skills eintragen
- Adapter-Healthchecks definieren
- Offline-Fallbacks dokumentieren

## Phase 3: Windows-App-Grundlage (CORE-11 bis CORE-15)

### CORE-11: Windows-App-Architektur finalisieren
- Entscheidung WinUI 3 vs. WebView2 vs. WPF
- Projektstruktur anlegen
- Build-Prozess definieren

### CORE-12: UI-Grundlagen implementieren
- Hauptfenster
- Dreiansicht (Original / OCR / Übersetzung)
- Sekretariatsansicht
- Anwaltsansicht

### CORE-13: Barrierefreiheit umsetzen
- Tastaturbedienung
- Kontrast
- Skalierung
- Screenreader-Unterstützung

### CORE-14: Deployment vorbereiten
- MSIX-Paketierung prüfen
- Offline-Installation vorbereiten
- Gerichtslaptop-Profil testen

### CORE-15: Info-Buttons und Hilfe
- Feldhilfen implementieren
- Buttonhilfen implementieren
- Warnhinweise implementieren
- Kontext-Hilfe

## Phase 4: Test und Abnahme (CORE-16 bis CORE-20)

### CORE-16: Teststrategie umsetzen
- Testkatalog erstellen
- Testdaten-Regeln definieren
- Regressionstests automatisieren

### CORE-17: Build und Release
- Versionsnummern vergeben
- Changelog führen
- Release-Checkliste erstellen

### CORE-18: Backup und Restore
- Backup-Konzept umsetzen
- Restore-Testplan durchführen
- Integritätsprüfung

### CORE-19: Rechte und Rollen
- Rollenmodell implementieren
- Berechtigungen prüfen
- Freigaberegeln definieren

### CORE-20: Datenschutz und Mandatsgeheimnis
- Datenschutz-Markierungen umsetzen
- Mandatsgeheimnis-Regeln prüfen
- Exportregeln definieren

## Empfohlene Reihenfolge

1. CORE-01 (Register befüllen)
2. CORE-02 (Statusmodell)
3. CORE-03 (Schnittstellen)
4. CORE-04 (Healthcheck)
5. CORE-05 (Resolver)
6. CORE-06 (Altbestand inventarisieren)
7. CORE-07 bis CORE-10 (Altbestand anbinden)
8. CORE-11 bis CORE-15 (Windows-App)
9. CORE-16 bis CORE-20 (Test und Abnahme)

Geschätzte Gesamtdauer: 12–16 Wochen.
