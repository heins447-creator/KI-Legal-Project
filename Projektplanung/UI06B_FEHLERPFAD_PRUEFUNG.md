# UI06b – Fehlerpfadprüfung der Gesamtkette

## Ziel

Erweitert UI06 um systematische Fehlerpfadprüfung. Statt eines einzelnen Musterlaufs werden 5 Szenarien durchgespielt, um sicherzustellen, daß die Kette in jedem Zustand korrekt reagiert.

## Szenarien

| Szenario | Name | Beschreibung | Erwartetes Ergebnis |
|----------|------|--------------|---------------------|
| A | Happy Path | Alles OK, keine Fehler | P3 Entscheidung freigeben |
| B | OCR-Fehler | Ein Dokument fehlerhaft | P0 OCR-Fehler prüfen (blockierend) |
| C | Türschwelle ablehnen | Nicht mandatsfähig | Prozeß stoppt vor Mandantenakte |
| D | UI04b Plausibilitätsfehler | Entscheidung fehlerhaft | P3 Entscheidungsmaske korrigieren (blockierend) |
| E | Mehrfachblockade | OCR-Fehler + Argos fehlt + UI04b Warnung | P0 blockierend, Übersetzung gesperrt, P3 mit Warnung |

## Prüfkriterien pro Szenario

1. **Station 1 (Posteingang)** – Dokumente korrekt erkannt
2. **Station 2 (Türschwelle)** – Mandatsfähigkeit korrekt bewertet
3. **Station 3 (Mandantenakte)** – OCR/Übersetzung/Freigabe korrekt
4. **Station 4 (Arbeitszentrale)** – Aktionen korrekt priorisiert
5. **Sperrregister** – Gesperrte Module nicht ausgelöst
6. **Grenzen** – Keine DB/Internet/Cloud/Originaländerung

## Dateien

- `Scripts/python_runner/ui06b_fehlerpfad_pruefung.py`
- `Scripts/python_runner/check_ui06b_fehlerpfad_pruefung.py`
- `Scripts/UI06B_FEHLERPFAD_PRUEFUNG_AUTOLAUF.ps1`
- `Projektplanung/UI06B_FEHLERPFAD_PRUEFUNG.md`

## Nächster Auftrag

- UI07: Deployment-/Betriebsvorbereitung (nach erfolgreicher Fehlerpfadprüfung)

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| v1 | 2026-05-17 | Erstellerstellung |
