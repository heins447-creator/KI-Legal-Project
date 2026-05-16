# KM21b-0 – Argos-Modellbereitstellung vorbereiten, ohne Download

## Zweck

Vorbereitet die kontrollierte Ablage, Prüfung und Freigabe von `.argosmodel`-Dateien für die spätere lokale Übersetzung. Es werden **keine Modelle heruntergeladen**, **keine Cloud-Verbindung aufgebaut** und **keine Installation durchgeführt**.

## Was erzeugt wird

| Ausgabe | Zweck | Ort |
|---------|-------|-----|
| Ablageordner `Models/` | Freigegebene Modelle (nach Prüfung) | `Tools/Translation/Models/` |
| Ablageordner `Manifests/` | SHA256-Manifeste pro Modell | `Tools/Translation/Manifests/` |
| Ablageordner `Licenses/` | Lizenz-/Quellennachweise | `Tools/Translation/Licenses/` |
| Ablageordner `Incoming/` | Neue Modelle zur Prüfung | `Tools/Translation/Incoming/` |
| Ablageordner `Rejected/` | Abgelehnte Modelle | `Tools/Translation/Rejected/` |
| Manifest-Schema JSON | Prüfregeln und Felddefinitionen | `Agentensteuerung/21b0_Argos_Modellbereitstellung/07_Manifest/KM21b0_MANIFEST_SCHEMA.json` |
| Importanleitung TXT | Schritt-für-Schritt-Anleitung | `Agentensteuerung/21b0_Argos_Modellbereitstellung/03_Berichte/KM21b0_IMPORTANLEITUNG.txt` |
| Dummy-Manifest JSON | Vorlage für neues Modell | `Tools/Translation/Manifests/ARGOS_XX_YY_TEMPLATE.json` |
| Status-JSON | Gesamtstatus der Vorbereitung | `Agentensteuerung/21b0_Argos_Modellbereitstellung/02_Status/KM21b0_STATUS.json` |
| Bericht TXT | Zusammenfassung | `Agentensteuerung/21b0_Argos_Modellbereitstellung/03_Berichte/KM21b0_BERICHT.txt` |

## Importweg (später, manuell)

```text
1. Modell in Incoming/ ablegen
2. Lizenz-/Quellennachweis in Licenses/ ablegen
3. Manifest-JSON nach Schema in Manifests/ anlegen
4. KM21b ausführen (prüft SHA256, Sprachpaar, Lizenz)
5. Bei Erfolg: Modell nach Models/ verschieben
6. Bei Ablehnung: Modell nach Rejected/ verschieben, Grund dokumentieren
```

## Manifest-Schema (Prüfpunkte)

| Prüfpunkt | Beschreibung |
|-----------|-------------|
| SHA256-Hash | Muss vorhanden und abgleichbar sein |
| Dateigröße | > 0 Byte |
| Sprachpaar | Im Dateinamen oder Metadaten erkennbar (Format: `xx_YY`) |
| Lizenznachweis | Muss vorhanden sein |
| Quellennachweis | Sollte vorhanden sein |
| Keine Cloud-URL | In Metadaten keine Download-URL |

## Ablehnungsgründe

- Hash stimmt nicht überein
- Datei beschädigt (0 Byte oder unlesbar)
- Lizenz fehlt oder unklar
- Quelle unbekannt oder nicht verifizierbar
- Cloud-Abhängigkeit erkennbar

## Liefergegenstände

| Datei | Zweck |
|-------|-------|
| `Scripts/python_runner/km21b0_argos_modellbereitstellung.py` | Python-Läufer |
| `Scripts/python_runner/check_km21b0_argos_modellbereitstellung.py` | Prüfdatei (15+ Checks) |
| `Scripts/KM21b0_ARGOS_MODELLBEREITSTELLUNG_AUTOLAUF.ps1` | PowerShell-Starter |
| `Config/km21b0_argos_modellbereitstellung_v1.json` | Konfiguration |
| `Projektplanung/KM21b0_ARGOS_MODELLBEREITSTELLUNG.md` | Diese Dokumentation |

## Grenzen

- ✓ **Kein Download**
- ✓ **Kein Internet**
- ✓ **Keine Cloud**
- ✓ **Keine Installation**
- ✓ **Keine Status-Änderung** (Argos bleibt „nicht verfügbar")
- ✓ **Keine echte Übersetzung**
- ✓ **Keine DB-Änderung**
- ✓ **Keine Registeränderung** (nur lesend)
- ✓ **Nur Vorbereitung**

## Abhängigkeiten

- CORE-11-Register (toolregister.json, ressourcenregister.json) – nur lesend

## Nächster Schritt nach KM21b-0

1. **Manuelle Bereitstellung:** `.argosmodel`-Dateien in `Tools/Translation/Incoming/` ablegen
2. **KM21b ausführen:** Inventarisierung, SHA256-Prüfung, Lizenzprüfung, Registerzuordnung
3. **Erst nach erfolgreicher KM21b-Prüfung:** Status auf „vorbereitet/freigegeben" setzen
