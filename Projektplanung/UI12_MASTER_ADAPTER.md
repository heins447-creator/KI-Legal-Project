# UI12 – Kombinierter Master-Adapter

## Zweck

UI12 führt die Ergebnisse von **UI10 (Profil-Leseadapter)** und **UI11 (Register-Leseadapter)** zu einer **zentralen Systemansicht** zusammen. Dabei werden Profilstatus, Grundschalter, Sperrstatus, Ressourcenstatus, Toolstatus, Quellenstatus, Lizenzstatus, Update-Alter, Modulstatus, kritische Blockaden, Warnungen und zulässige nächste Schritte in einem einzigen Adapter-JSON bereitgestellt.

UI12 dient als **einziger Einstiegspunkt** für künftige Module, die vor ihrer Aktivierung das Gesamtsystem prüfen müssen.

## Freeze-Kompatibilität

| Kriterium | Wert |
|-----------|------|
| Berührt UI03–UI07b | **Nein** |
| Nur lesend auf UI09, UI10, UI11 | **Ja** |
| Neue Dateien | **Ja** |
| produktiv_freigegeben | **false** |
| nur_musterdaten | **true** |
| echte_daten_erlaubt | **false** |

## Architektur

```
┌─────────────────────────────────────────┐
│  UI12 – Kombinierter Master-Adapter     │
│  (einziger Einstieg für neue Module)    │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┴───────────────┐
    ▼                               ▼
┌──────────────┐            ┌──────────────┐
│ UI10 Profil  │            │ UI11 Register│
│  -Adapter    │            │  -Adapter    │
│  (JSON)      │            │  (JSON)      │
└──────────────┘            └──────────────┘
    │                               │
    ▼                               ▼
┌──────────────┐            ┌──────────────┐
│ UI09 Profil- │            │ 8 Register:  │
│  felder +    │            │ Sperr, Res-  │
│  Grundschalter│           │ sourcen, Tool│
│  (JSON)      │            │ Quellen,     │
└──────────────┘            │ Lizenz,      │
                            │ Update,      │
                            │ Modul, Skill │
                            └──────────────┘
```

## Eingaben

| Quelle | Pfad | Zweck |
|--------|------|-------|
| UI10 Profil-Adapter | `Windows_App/Logs/UI10_PROFIL_ADAPTER.json` | Profilstatus, Grundschalter |
| UI11 Register-Adapter | `Windows_App/Logs/UI11_REGISTER_ADAPTER.json` | Alle 8 Register-Status |
| UI09 Grundschalter | `Windows_App/Logs/UI09_GRUNDSCHALTER.json` | Zentrale Schalter |
| UI09 Profilfelder | `Windows_App/Logs/UI09_PROFILFELDER.json` | Profilfelder |

Sind die Eingaben nicht vorhanden, arbeitet UI12 mit **Musterdaten** und erzeugt Warnungen.

## Kombinationsregeln (KOMB_01 – KOMB_08)

| Regel | Name | Status bei Verletzung | Beschreibung |
|-------|------|----------------------|--------------|
| KOMB_01 | Profil-Register-Konsistenz | **WARNUNG** | Aktives Profilfeld ohne passenden Register-Eintrag |
| KOMB_02 | Sperrstatus dominiert Profil | **BLOCKADE** | Sperrregister-Eintrag hat Vorrang vor Grundschaltern |
| KOMB_03 | Lizenz-Register-Abgleich | **BLOCKADE** | Ungültige/abgelaufene Lizenz blockiert Module |
| KOMB_04 | Update-Alter-Warnung | **WARNUNG / BLOCKADE** | Alter > 90 Tage (Warnung), > 180 Tage (Blockade) |
| KOMB_05 | Ressourcen-Tool-Konsistenz | **WARNUNG** | Benötigte Ressource/Tool nicht aktiv |
| KOMB_06 | Skill-Quellen-Konsistenz | **WARNUNG** | Benötigter Skill oder Quelle nicht verfügbar |
| KOMB_07 | Demo-Modus-Blockade | **BLOCKADE** | Kritische Schritte im Demo-Modus blockiert |
| KOMB_08 | Grundschalter-Gesamtausschluss | **BLOCKADE** | GS01 oder GS08 auf false blockiert System |

## Nächste Schritte-Logik

| Bedingung | Zulässige Schritte | Hinweis |
|-----------|-------------------|---------|
| Blockaden = 0, Warnungen = 0 | UI03-1b … UI08 | System vollständig bereit |
| Blockaden = 0, Warnungen > 0 | UI03-1b … UI08 | System bereit – Prüfung empfohlen |
| Blockaden > 0 | UI08b … UI12 | Nur Sanierungsmodule zulässig |

## Ausgaben

| Datei | Pfad |
|-------|------|
| Master-Adapter JSON | `Windows_App/Logs/UI12_MASTER_ADAPTER.json` |
| HTML-Bericht | `Windows_App/Logs/UI12_MASTER_ADAPTER.html` |
| Text-Bericht | `Windows_App/Logs/UI12_MASTER_ADAPTER_BERICHT.txt` |
| Konsistenzlog | `Windows_App/Logs/UI12_KONSISTENZLOG.json` |

## Lieferpflicht (AGENTS.md)

- [x] Config: `Config/ui12_master_adapter_v1.json`
- [x] Python-Läufer: `Scripts/python_runner/ui12_master_adapter.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui12_master_adapter.py`
- [x] PowerShell-Starter: `Scripts/UI12_MASTER_ADAPTER_AUTOLAUF.ps1`
- [x] Dokumentation: `Projektplanung/UI12_MASTER_ADAPTER.md`
- [x] Testlauf: Erfolgreich
- [x] Bericht: `Windows_App/Logs/UI12_MASTER_ADAPTER_BERICHT.txt`

## Sperrregister

UI12 prüft vor dem Start das Sperrregister (`ALIN_Neustart_Core/01_Register/sperrregister.json`).
Bei Sperrung wird die Ausführung abgebrochen.

## Abhängigkeiten

| Modul | Zweck |
|-------|-------|
| UI09 | Zentrale Grundschalter und Profilfelder |
| UI10 | Profil-Leseadapter (bereits kombiniert) |
| UI11 | Register-Leseadapter (bereits kombiniert) |

## Autor

ALIN System | Version 1.0.0 | Status: Entwurf | Demo-Modus

## Changelog

| Datum | Änderung |
|-------|----------|
| 2026-05-17 | Erstversion UI12 Master-Adapter |
