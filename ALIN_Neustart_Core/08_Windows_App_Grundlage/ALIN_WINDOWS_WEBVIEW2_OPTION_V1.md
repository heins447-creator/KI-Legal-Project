# ALIN Windows-WebView2-Option V1

## Zweck

WebView2 als Übergangslösung für bestehende HTML-Prüfansichten (UI01, UI04).

## Vorteile

- Bestehende HTML-Prototypen können sofort genutzt werden
- Schrittweise Migration zu WinUI 3 möglich
- Geringerer initialer Entwicklungsaufwand

## Nachteile

- Zusätzliche Komplexität durch Host-WebView-Kommunikation
- Abhängigkeit von Edge-Chromium
- Performance-Overhead
- Barrierefreiheit schwieriger als native UI

## Kommunikation Host ↔ WebView2

- `ExecuteScriptAsync` für Aufrufe aus Host in WebView2
- `WebMessageReceived` für Nachrichten aus WebView2 an Host
- JSON als Nachrichtenformat

## Empfohlene Vorgehensweise

1. **Phase 1:** WebView2 für UI01 und UI04
2. **Phase 2:** Schrittweise Migration einzelner Ansichten zu WinUI 3
3. **Phase 3:** Vollständige WinUI 3-Implementierung

## Entscheidung

WebView2 als kurzfristige Übergangslösung akzeptabel, langfristig WinUI 3 anstreben.
