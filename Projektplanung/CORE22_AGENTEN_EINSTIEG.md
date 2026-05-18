# CORE-22 – Agenten-Einstieg und Arbeitsregel-Erzwingung

## Ziel

Verbindliche Agentenregel und Startprüfung für Roo, damit vor jedem neuen Auftrag geprüft wird:

1. Arbeitsindex vorhanden?
2. Startpunkt vorhanden?
3. Arbeitsbereich freigegeben?
4. Pfad gesperrt oder nur Referenz?
5. Auftrag betrifft Altbestand oder Neustart-Core?
6. Darf geschrieben werden oder nur gelesen?

## Regelwerk

### Vor jedem Auftrag

```text
1. Arbeitsindex vorhanden prüfen     → Config/core21_arbeitsindex_v1.json
2. Startpunkt vorhanden prüfen        → ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md
3. Zielpfad in bereich_status() prüfen
4. Bei 'aktiv'    → Schreiben erlaubt
5. Bei 'referenz' → NUR lesen, NICHT schreiben
6. Bei 'gesperrt' → ABLEHNEN
7. Bei 'unbekannt'→ NACHFRAGEN oder als Archiv behandeln
```

### Bereichsstatus

| Status     | Bedeutung                 | Schreiben | Lesen |
|------------|---------------------------|-----------|-------|
| `aktiv`    | Aktiver Arbeitsbestand    | Ja        | Ja    |
| `referenz` | Referenz, nicht mehr aktiv| Nein      | Ja    |
| `gesperrt` | Gesperrt, nicht bearbeiten| Nein      | Nein  |
| `unbekannt`| Nicht im Arbeitsindex     | Nein      | Vorsicht |

### Aktive Bereiche

- `ALIN_Neustart_Core/00_Dokumentation/`
- `ALIN_Neustart_Core/01_Register/`
- `ALIN_Neustart_Core/02_Statusmodell/`
- `ALIN_Neustart_Core/03_Schnittstellen/`
- `ALIN_Neustart_Core/04_Healthcheck/`
- `ALIN_Neustart_Core/05_Resolver/`
- `ALIN_Neustart_Core/06_Audit_Protokoll/`
- `ALIN_Neustart_Core/10_Update_Ueberwachung/`
- `ALIN_Neustart_Core/12_Dokumentation_Hilfe_Infofelder/`
- `ALIN_Neustart_Core/13_Anforderungen_Abnahme/`
- `ALIN_Neustart_Core/14_Architekturentscheidungen/`
- `ALIN_Neustart_Core/15_Teststrategie/`
- `ALIN_Neustart_Core/23_Import_Export/`
- `ALIN_Neustart_Core/24_Konfigurationsprofile/`
- `ALIN_Neustart_Core/Config/`
- `ALIN_Neustart_Core/Scripts/`
- `ALIN_Neustart_Core/Reports/`
- `Projektplanung/`
- `Scripts/python_runner/`
- `Config/`
- `Database/Migrations/`
- `Windows_App/`

### Referenz-Bereiche (nur lesen)

- `ALIN_Neustart_Core/07_Bestandsaufnahme_Altbestand/`
- `ALIN_Neustart_Core/08_Migration/01_Plaene/`
- `ALIN_Neustart_Core/08_Migration/02_Kopierte_Dateien/`
- `ALIN_Neustart_Core/08_Migration/09_Manifest/`
- `Agentensteuerung/`
- `07_Berichte/`
- `10_Tool_Inventar/`

### Gesperrte Kategorien

- `gesperrt`
- `manuell`
- `archiv`
- `dublette`
- `testrest`
- `laufzeit`

## Verbotene Operationen

- Löschen im Altbestand
- Verschieben im Altbestand
- Umbenennen im Altbestand
- Schreiben in referenz/ oder gesperrt/
- Echte Mandantendaten an externe Modelle
- API-Schlüssel in Git

## Erste Lesedateien

1. `ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md`
2. `ALIN_Neustart_Core/00_Dokumentation/ALIN_MODULPAKETE.md`
3. `ALIN_Neustart_Core/00_Dokumentation/ALIN_PROFESSIONELLE_SOFTWARE_KONSTRUKTION.md`

## Dateien

- Runner: `Scripts/python_runner/core22_agenten_einstieg.py`
- Check: `Scripts/python_runner/check_core22_agenten_einstieg.py`
- Starter: `Scripts/CORE22_AGENTEN_EINSTIEG_AUTOLAUF.ps1`
- Regeln: `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json`
- Bericht: `ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt`
- Dokumentation: `Projektplanung/CORE22_AGENTEN_EINSTIEG.md`
- Konfiguration: `Config/core22_agentenregeln_v1.json`

## Abhängigkeiten

- CORE-21 (Arbeitsindex)
- CORE-14 bis CORE-20 (Migration)

## Status

- `nur_regelnd` – keine destruktiven Operationen
- `produktiv_freigegeben` = false
