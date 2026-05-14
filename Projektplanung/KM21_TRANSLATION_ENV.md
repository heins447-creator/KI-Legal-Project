# KM21 – Lokale Übersetzungsumgebung vorbereiten — DOKUMENTATION

## Baustein
KM21 inventarisiert und prüft die lokale Übersetzungsumgebung unter Tools\Translation,
ohne Internet, ohne Installation, ohne Cloud. Es bereitet die Schnittstelle für KM15 vor.

## Technik
- Sprache: Python 3.12
- Keine externen Bibliotheken außer stdlib (json, csv, pathlib, shutil)
- Argos Translate wird nur importiert, wenn bereits im System installiert
- Rein lesend bis auf Verzeichnisstruktur unter Tools\Translation

## Dateien

| Datei | Pfad |
|---|---|
| Konfiguration | Config/km21_translation_env_v1.json |
| Python-Läufer | Scripts/python_runner/km21_translation_env_prepare.py |
| Prüfdatei | Scripts/python_runner/check_km21_translation_env_prepare.py |
| PowerShell-Starter | Scripts/KM21_TRANSLATION_ENV_AUTOLAUF.ps1 |
| Dokumentation | Projektplanung/KM21_TRANSLATION_ENV.md |

## Ausgaben (Bereich: Agentensteuerung/21_Translation_Environment)

| Datei | Pfad |
|---|---|
| Status | 02_Status/KM21_STATUS.json |
| Bericht | 03_Berichte/KM21_BERICHT.txt |
| Fehler | 05_Fehler/KM21_FEHLER.txt |
| Manifest JSON/CSV | 07_Manifest/KM21_MANIFEST.* |
| Inventar JSON/CSV | 08_Inventar/KM21_TRANSLATION_INVENTAR.* |
| Dummy-Test | 09_Test/KM21_DUMMY_TRANSLATION_TEST.json |
| KM15-Interface JSON/MD | 10_Schnittstelle_KM15/KM21_KM15_TRANSLATION_INTERFACE.* |
| Ausführungsnotiz | 13_Ausfuehrungsnotizen/KM21_AUSFUEHRUNGSNOTIZ.txt |

## Verzeichnisse

| Pfad | Zweck |
|---|---|
| Tools/Translation/Argos | Argos-Translate-spezifische Skripte |
| Tools/Translation/Models | Sprachmodelle (.argosmodel) |
| Tools/Translation/Packages | Python-Pakete |
| Tools/Translation/Test | Testdaten |
| Tools/Translation/Logs | Übersetzungsprotokolle |
| Tools/Translation/Cache | Übersetzungscache |

## Grenzen
- Keine Installation, kein Internet, keine Cloud, keine API
- Keine echten Aktenübersetzungen
- Keine Originaländerung, keine DB-Änderung
- Keine Rechtsbewertung

## Start
```
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "I:\KI_Legal_Project\Scripts\KM21_TRANSLATION_ENV_AUTOLAUF.ps1"
```
