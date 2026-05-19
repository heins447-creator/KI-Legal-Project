# ADR 0001: Windows-App-Grundlage

## Kontext

ALIN benötigt eine moderne Windows-Desktop-Anwendung.

## Entscheidung

WinUI 3 als primäre Technologie, WebView2 als Übergangslösung.

## Begründung

- WinUI 3 ist die modernste Microsoft-Technologie.
- Native Leistung, Fluent Design, gute Barrierefreiheit.
- WebView2 ermöglicht schrittweise Migration bestehender HTML-Ansichten.

## Konsequenzen

- Windows 10 1809+ / Windows 11 erforderlich.
- Entwicklung erfordert Windows App SDK.
