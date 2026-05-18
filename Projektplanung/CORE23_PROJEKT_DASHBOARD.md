# CORE-23: Arbeitsstart-Zentrale / Projekt-Dashboard

## Ziel
Eine einzige Übersicht, die beim Start zeigt:
- Aktiver Arbeitsbestand
- Referenzbereiche
- Gesperrte Bereiche
- Letzter Migrationsstand
- Offene manuelle Prüfungen
- Gesperrte Restdateien
- Zulässige nächste Arbeiten
- Blockierte Arbeiten
- Startpunkt für Roo
- Status CORE-13 bis CORE-22

## Datenquellen
| Quelle | Pfad |
|--------|------|
| CORE21 Manifest | `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE21_arbeitsindex.json` |
| CORE22 Manifest | `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE22_agenten_regeln.json` |
| CORE19 Plan | `ALIN_Neustart_Core/08_Migration/01_Plaene/CORE19_reste_archiv_sperrplan.json` |
| CORE20 Bericht | `ALIN_Neustart_Core/Reports/CORE20_MASTER_UMBAU_BERICHT.txt` |
| CORE21 Bericht | `ALIN_Neustart_Core/Reports/CORE21_ARBEITSINDEX_BERICHT.txt` |
| CORE22 Bericht | `ALIN_Neustart_Core/Reports/CORE22_AGENTEN_EINSTIEG_BERICHT.txt` |
| Config CORE21 | `Config/core21_arbeitsindex_v1.json` |
| Config CORE22 | `Config/core22_agentenregeln_v1.json` |

## Ergebnisse
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.json`
- `ALIN_Neustart_Core/08_Migration/09_Manifest/CORE23_dashboard.html`
- `ALIN_Neustart_Core/Reports/CORE23_PROJEKT_DASHBOARD_BERICHT.txt`

## Dateien
- **Runner:** `Scripts/python_runner/core23_projekt_dashboard.py`
- **Check:** `Scripts/python_runner/check_core23_projekt_dashboard.py`
- **Starter:** `Scripts/CORE23_PROJEKT_DASHBOARD_AUTOLAUF.ps1`
- **Config:** `Config/core23_dashboard_v1.json`
- **Doku:** `Projektplanung/CORE23_PROJEKT_DASHBOARD.md` (diese Datei)

## Nutzung
```powershell
Scripts\CORE23_PROJEKT_DASHBOARD_AUTOLAUF.ps1
```

Oder manuell:
```
python Scripts\python_runner\core23_projekt_dashboard.py
python Scripts\python_runner\check_core23_projekt_dashboard.py
```

## Startpunkt für Roo
1. Config/core21_arbeitsindex_v1.json laden
2. ALIN_Neustart_Core/00_Dokumentation/ALIN_MASTERAUFTRAG_NEUSTART_CORE_01.md lesen
3. ALIN_Neustart_Core/00_Dokumentation/ALIN_AUFTRAGSINDEX.md lesen
4. Bereichsstatus prüfen vor jedem Schreibzugriff
5. Dashboard als Orientierung nutzen
