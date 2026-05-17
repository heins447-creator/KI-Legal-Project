# UI06 – Musterlauf Gesamtkette

## Ziel

Simuliert den vollständigen Prozeß von Posteingang bis zur UI05-Arbeitszentrale als durchgängigen Musterlauf mit Musterdaten.

## Prozeßkette

```
Posteingang -> Türschwelle -> Mandantenakte (OCR/Übersetzung/Freigabe) -> UI05-Arbeitszentrale
```

## Stationen

### Station 1: Posteingang

- Dokumente werden registriert
- Absender, Verfahrensnummer, Dringlichkeit erfaßt
- Ausgabe: `UI06_01_POSTEINGANG.json`

### Station 2: Türschwelle

- Mandatsfähigkeit geprüft
- Risiko eingeschätzt
- Entscheidung: annehmen / ablehnen
- Sperrregister-Prüfung
- Ausgabe: `UI06_02_TUERSCHWELLE.json`

### Station 3: Mandantenakte

- OCR-Status pro Dokument
- Übersetzungsprüfung (Argos-Modelle fehlen -> geparkt)
- Freigabe-Status
- Parkstatus
- Ausgabe: `UI06_03_MANDANTENAKTE.json`
- Kompatibilität: erzeugt auch `UI03_1g_GESAMTANSICHT_STATUS.json`

### Station 4: UI05-Arbeitszentrale

- Aktionen bestimmen (P0-P4)
- Sperrregister prüfen
- Ausgabe: `UI06_04_ARBEITSZENTRALE.json`
- Kompatibilität: erzeugt auch `UI04b_STATUS.json`

## Musterdaten

| Dokument | Sprache | Seiten | OCR-Status |
|----------|---------|--------|------------|
| Muster_Klageerwiderung.pdf | de | 12 | ok |
| Muster_Beweismittelverzeichnis_EN.pdf | en | 8 | ok |
| Muster_Gerichtsbescheid_SV.pdf | sv | 4 | fehlerhaft (Tesseract SV fehlt) |

## Erwartete Ergebnisse

- **OCR**: 2/3 OK, 1 Fehler (SV-Dokument)
- **Übersetzung**: Gesperrt (Argos-Modelle fehlen)
- **Freigabe**: Ausstehend (OCR-Fehler)
- **Nächste Aktion**: P0 OCR-Fehler prüfen (blockierend)
- **Gesperrt**: Übersetzung (KM21b), kritische Module

## Grenzen

- Keine Originaländerung
- Keine neue OCR
- Keine DB-Änderung
- Kein Internet/Cloud
- Keine endgültige Übersetzung behauptet
- Keine Rechtsbewertung
- Keine Beweiswürdigung
- Gesperrte Aktionen nicht auslösen
- Nur Musterdaten verwendet

## Dateien

- `Config/ui06_musterlauf_gesamtkette_v1.json`
- `Scripts/python_runner/ui06_musterlauf_gesamtkette.py`
- `Scripts/python_runner/check_ui06_musterlauf_gesamtkette.py`
- `Scripts/UI06_MUSTERLAUF_GESAMTKETTE_AUTOLAUF.ps1`
- `Agentensteuerung/UI06_Musterlauf_Gesamtkette/`

## Nächster Auftrag

- UI07: Produktivfreigabe und Deployment-Vorbereitung
- Oder: Integration mit echten Daten (nach Freigabe)

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| v1 | 2026-05-17 | Erstellerstellung |
