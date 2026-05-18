# ALIN Windows-App-Architektur V1

## Ziel

Dokumentation der Windows-App-Grundlage für ALIN. Noch keine Programmierung, nur Vorbereitung.

## Trennung ALIN-Core und ALIN-Windows

| Schicht | Technologie | Zweck |
|---------|-------------|-------|
| ALIN-Windows (UI) | WinUI 3 / WebView2 | Darstellung, Bedienung, Kanzleisprache |
| UI-Adapter | C# / .NET | Übersetzung zwischen UI und Core |
| ALIN-Core | Python | Register, Resolver, Status, Schnittstellen, Healthcheck |
| Infrastruktur | Python / DuckDB | Datenbank, Dateisystem, Tools |

## Architektur-Optionen

### Option A: WinUI 3 (empfohlen)
- Modernste Microsoft-Technologie für Windows-Desktop-Apps
- Windows App SDK erforderlich
- Native Leistung, Fluent Design, gute Barrierefreiheit
- Nachteil: Erfordert Windows 10 1809+ / Windows 11

### Option B: WebView2 (Übergangslösung)
- Hostet bestehende HTML-Prüfansichten (UI01, UI04)
- Ermöglicht schrittweise Migration
- Nachteil: Zusätzliche Komplexität durch Host-WebView-Kommunikation

### Option C: WPF / WinForms
- Nur als Integrations- oder Übergangsschicht
- Nicht für neue Entwicklung empfohlen

## Empfohlene Entscheidung

**Primär: WinUI 3**
**Übergang: WebView2 für bestehende HTML-Ansichten**
**Langfristig: Vollständige WinUI 3-Migration**

## Fensterverwaltung

- Hauptfenster mit Navigation
- Dreiansicht: Original / OCR / Übersetzung
- Vollbild-Modus für Dokumente
- Geteilte Ansicht für Vergleiche
- Skalierung: 100 % bis 200 %
- Kontrast: Hoher Kontrast unterstützt

## Lokale Ressourcen

- Programm, Daten, Cache, Logs getrennt
- Offline-Betrieb ohne Internet
- Gerichtslaptop-Profil

## Deployment

- MSIX oder zulässiges Modell
- Kanzlei-PC und Gerichtslaptop
- Trennung Programm / Daten / Cache / Logs

## Nächste Schritte

1. Entscheidung WinUI 3 vs. WebView2 finalisieren
2. Projektstruktur anlegen
3. Build-Prozess definieren
4. UI-Grundlagen implementieren
