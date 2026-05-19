# CORE-10f – Platzhalter-Eingabe/Ausgabe verfeinern

## Zweck

48 PowerShell-Starter im [`modulregister.json`](ALIN_Neustart_Core/01_Register/modulregister.json) hatten identische generische Platzhalter-Beschreibungen:

- **Eingabe:** "Konfiguration und Umgebungsvariablen."
- **Ausgabe:** "Prozess-Start, Log-Datei, Exit-Code."

Diese Beschreibungen sagten nichts über den tatsächlichen Zweck des Moduls aus und erschwerten Wartung, Fehlersuche und Schnittstellen-Abstimmung.

## Durchführung

1. **Analyse:** Alle 163 Modul-Einträge im Modulregister geprüft.
2. **Mapping:** 48 PowerShell-Starter anhand ihrer `modul_id` modulspezifischen Beschreibungen zugeordnet.
3. **Kategorien:**
   - OCR / Arbeitsabbildung (11 Module)
   - Übersetzung (2 Module)
   - Agenten (6 Module)
   - Posteingang / Vorzimmer (7 Module)
   - Quellen / Rechtsquellen (3 Module)
   - UI / Anwalt / Mandant (8 Module)
   - Tools / External / Hilfsskripte (11 Module)
4. **Register-Update:** `eingabe` und `ausgabe` der 48 Module überschrieben.

## Ergebnis

| Kennzahl | Wert |
|---|---|
| Verfeinerte Einträge | 48 |
| Unveränderte Einträge | 115 |
| Generische Platzhalter übrig | 0 |

## Grenzen

- Keine Änderung an PowerShell-Skripten selbst (nur Register-Metadaten).
- Beschreibungen basieren auf Modulnamen-Inferenz, nicht auf tatsächlicher Code-Analyse.
- Keine funktionale Änderung, nur Dokumentationsverbesserung.

## Dateien

- [`ALIN_Neustart_Core/01_Register/modulregister.json`](ALIN_Neustart_Core/01_Register/modulregister.json) – aktualisiert
- [`ALIN_Neustart_Core/Scripts/alin_core10f_platzhalter_verfeinern.py`](ALIN_Neustart_Core/Scripts/alin_core10f_platzhalter_verfeinern.py)
- [`ALIN_Neustart_Core/Scripts/alin_core10f_pruefung.py`](ALIN_Neustart_Core/Scripts/alin_core10f_pruefung.py)
- [`ALIN_Neustart_Core/Scripts/Run_CORE10f_Platzhalter_Verfeinern.ps1`](ALIN_Neustart_Core/Scripts/Run_CORE10f_Platzhalter_Verfeinern.ps1)
- [`ALIN_Neustart_Core/Reports/ALIN_CORE10F_PLATZHALTER_BERICHT.txt`](ALIN_Neustart_Core/Reports/ALIN_CORE10F_PLATZHALTER_BERICHT.txt)
- [`ALIN_Neustart_Core/Reports/ALIN_CORE10F_PRUEFBERICHT.txt`](ALIN_Neustart_Core/Reports/ALIN_CORE10F_PRUEFBERICHT.txt)
- Diese Datei

## FOLGEAUFTRÄGE

- [ ] CORE-10g: P06/P07 Reviewlisten dokumentieren (DB-ändernde und online-fähige Module)
