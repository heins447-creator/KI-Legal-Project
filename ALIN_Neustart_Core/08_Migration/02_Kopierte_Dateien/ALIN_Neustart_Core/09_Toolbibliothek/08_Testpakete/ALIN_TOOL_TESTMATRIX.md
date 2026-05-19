# ALIN Tool-Testmatrix

## Testgruppen

### OCR
- Tesseract: Version, Sprachpakete, Funktionstest

### PDF
- PyMuPDF: Öffnen, Rendern, Extrahieren

### Bildverarbeitung
- OpenCV: Laden, Transformieren
- Pillow: Laden, Speichern

### Übersetzung
- Argos Translate: Modell laden, Übersetzen

### Datenbank
- DuckDB: Verbindung, Abfrage

### Sicherheit
- Windows Defender: Scan-Test
- SHA256: Hash-Berechnung

## Testfälle

| Tool | Testfall | Erwartet | Status |
|------|----------|----------|--------|
| Tesseract | Version abrufen | Versionsnummer | Offen |
| PyMuPDF | PDF öffnen | Kein Fehler | Offen |
| DuckDB | Verbindung herstellen | Erfolg | Offen |
