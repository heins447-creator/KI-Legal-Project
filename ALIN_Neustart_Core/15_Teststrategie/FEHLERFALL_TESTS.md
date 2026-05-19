# ALIN Fehlerfall-Tests

## Zweck

Systematisches Testen von Fehlerfällen.

## Fehlerfälle

| Fehlerfall | Test | Erwartet |
|------------|------|----------|
| Fehlende Datei | Posteingang ohne Datei | Hinweis |
| Beschädigte Datei | Korruptes PDF | Sperre |
| Unbekannte Sprache | Dokument in unbekannter Sprache | Warnung |
| Fehlendes Tool | Tesseract nicht installiert | Hinweis |
| Datenbankfehler | Verbindung unterbrochen | Fehler |
| Timeout | Langer OCR-Lauf | Abbruch |

## Dokumentation

Jeder Fehlerfall wird protokolliert.
