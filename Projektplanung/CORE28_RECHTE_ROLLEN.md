# CORE-28: Rechte und Rollen

## Ziel

Validiere die existierenden Dokumente im Bereich Rechte und Rollen:
- [`ROLLENMODELL.md`](ALIN_Neustart_Core/18_Rechte_Rollen/ROLLENMODELL.md)
- [`FREIGABEREGELN.md`](ALIN_Neustart_Core/18_Rechte_Rollen/FREIGABEREGELN.md)
- [`BERECHTIGUNGEN.schema.json`](ALIN_Neustart_Core/18_Rechte_Rollen/BERECHTIGUNGEN.schema.json)

## Liefergegenstände

1. **Konfiguration** – [`Config/core28_rechte_rollen_v1.json`](Config/core28_rechte_rollen_v1.json)
2. **Python-Runner** – [`Scripts/python_runner/core28_rechte_rollen.py`](Scripts/python_runner/core28_rechte_rollen.py)
3. **Check-Datei** – [`Scripts/python_runner/check_core28_rechte_rollen.py`](Scripts/python_runner/check_core28_rechte_rollen.py)
4. **PowerShell-Starter** – [`Scripts/CORE28_RECHTE_ROLLEN_AUTOLAUF.ps1`](Scripts/CORE28_RECHTE_ROLLEN_AUTOLAUF.ps1)
5. **Dokumentation** – diese Datei
6. **Bericht** – [`ALIN_Neustart_Core/Reports/CORE28_RECHTE_ROLLEN_BERICHT.txt`](ALIN_Neustart_Core/Reports/CORE28_RECHTE_ROLLEN_BERICHT.txt)

## Prüfungen des Runners

- **Datei-Existenz**: Alle drei Quelldateien vorhanden
- **Rollenmodell**: Pflichtfelder (`Rolle`, `Beschreibung`, `Berechtigungen`) vorhanden
- **Rollenmodell**: Alle erlaubten Rollen (`Sekretariat`, `Anwalt`, `Administrator`, `System`, `Agent`, `Entwickler`) definiert
- **Freigaberegeln**: Pflichtabschnitte (`Grundsatz`, `Regeln`, `Widerruf`) vorhanden
- **Berechtigungen-Schema**: Gültiges JSON
- **Berechtigungen-Schema**: Alle required Properties (`schema_version`, `berechtigung_id`, `rolle`, `aktion`, `erlaubt`)
- **Berechtigungen-Schema**: Alle erlaubten Rollen im Enum

## Abhängigkeiten

- [`Config/core28_rechte_rollen_v1.json`](Config/core28_rechte_rollen_v1.json)
- [`ALIN_Neustart_Core/18_Rechte_Rollen/ROLLENMODELL.md`](ALIN_Neustart_Core/18_Rechte_Rollen/ROLLENMODELL.md)
- [`ALIN_Neustart_Core/18_Rechte_Rollen/FREIGABEREGELN.md`](ALIN_Neustart_Core/18_Rechte_Rollen/FREIGABEREGELN.md)
- [`ALIN_Neustart_Core/18_Rechte_Rollen/BERECHTIGUNGEN.schema.json`](ALIN_Neustart_Core/18_Rechte_Rollen/BERECHTIGUNGEN.schema.json)

## Rote Linien

- Keine Löschung existierender Dateien
- Keine Änderung der Quelldateien in `18_Rechte_Rollen/`
- Nur Lesen und Validieren, keine Modifikation

## Ausführung

```powershell
Scripts\CORE28_RECHTE_ROLLEN_AUTOLAUF.ps1
```

Oder manuell:

```bash
python Scripts/python_runner/core28_rechte_rollen.py
```
