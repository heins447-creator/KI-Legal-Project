# EXT-002 – PaddleOCR / Layout-Analyse

## Ziel
Vorbereitung der OCR-Strecke mit PaddleOCR fuer komplexe Layouts.
Da PaddleOCR aktuell nicht im Projekt-Toolchain installiert ist, legt diese Stufe die Infrastruktur und synthetische Testdaten an.

## Abhaengigkeiten
- EXT-001 (DuckDB-Schema)
- KM21b0 (Argos-Modellbereitstellung)
- STUFE-008 (Posteingang-OCR)

## Sicherheitsregeln
- **Cloud verboten**: Kein Cloud-OCR-Service.
- **Offline**: Keine Internetverbindung waehrend OCR.
- **Nur lokale Modelle**: PaddleOCR-Modelle muessen lokal vorliegen.
- **Keine echten Daten**: Nur synthetische Test-PDFs und Platzhalter.

## Architektur
```
PDF-Eingang (lokal)
    |
    v
PaddleOCR (lokal, nach Installation)
    |-- Layout-Analyse (Tabellen, Spalten, Fussnoten)
    |-- Text-Erkennung
    |
    v
DuckDB (alin_ext001.ocr_ergebnisse)
```

## Dateien
| Datei | Zweck |
|-------|-------|
| `Scripts/python_runner/ext002_paddleocr_layout.py` | Runner: erzeugt synthetische OCR-Daten, Installations-Skript, Layout-Stub |
| `Scripts/python_runner/check_ext002_paddleocr_layout.py` | Check: prueft DuckDB, Tabellen, PaddleOCR-Verfuegbarkeit |
| `Scripts/EXT002_PADDLEOCR_LAYOUT_AUTOLAUF.ps1` | PowerShell-Autolauf |
| `Config/ext002_paddleocr_layout_v1.json` | Konfiguration |
| `Projektplanung/EXT002_PADDLEOCR_LAYOUT.md` | Diese Dokumentation |
| `ALIN_Neustart_Core/09_Toolbibliothek/01_Download_Quellen/PADDLEOCR_INSTALL.ps1` | Erzeugtes Offline-Installations-Skript |
| `ALIN_Neustart_Core/09_Toolbibliothek/02_PaddleOCR_Stub/alin_paddleocr_layout.py` | Erzeugter Layout-Analyse-Stub |

## Installationshinweis
PaddleOCR ist nicht automatisch installiert (kein Internet im Autolauf).
Um PaddleOCR manuell zu installieren:
```powershell
& ALIN_Neustart_Core\09_Toolbibliothek\01_Download_Quellen\PADDLEOCR_INSTALL.ps1
```

## Testlauf
Der Autolauf fuehrt folgende Schritte durch:
1. py_compile auf Runner und Check
2. Check prueft DuckDB-Tabellen
3. Runner erzeugt 6 synthetische OCR-Ergebnisse (Layout-Elemente)
4. Bericht wird geschrieben

## Aenderungshistorie
| Datum | Autor | Aenderung |
|-------|-------|----------|
| 2026-05-18 | ALIN-Agent | Erste Version |
