# UI13 – Abnahme- und Entscheidungsübersicht UI08–UI12

## Zweck

UI13 erzeugt eine **Browser-/HTML-Übersicht**, die den Gesamtstatus von **UI08 bis UI12** zusammenfasst. Sie dient als **Entscheidungsgrundlage** vor einer möglichen kontrollierten Öffnung des UI03–UI07b-Freeze.

Die Übersicht zeigt klar an:

- Welche Module sind abgeschlossen?
- Welche Adapter liefern Daten?
- Welche Eingaben fehlen noch?
- Welche Warnungen sind erwartbar?
- Welche Blockaden sind kritisch?
- Welche Schritte sind ohne Freeze-Öffnung zulässig?
- Welche Schritte würden UI03–UI07b berühren?

## Freeze-Kompatibilität

| Kriterium | Wert |
|-----------|------|
| Berührt UI03–UI07b | **Nein** |
| Nur lesend auf UI08–UI12 Ausgaben | **Ja** |
| Neue Dateien | **Ja** |
| produktiv_freigegeben | **false** |
| nur_musterdaten | **true** |
| echte_daten_erlaubt | **false** |

## Architektur

```
┌─────────────────────────────────────────┐
│ UI13 – Abnahme- und Entscheidungs-     │
│         übersicht UI08–UI12             │
│  (HTML-Browser-Ansicht als Dashboard)   │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌────────┐   ┌────────┐   ┌────────┐
│ UI08   │   │ UI10   │   │ UI12   │
│ UI08b  │   │ UI11   │   │ Master │
│ UI08c  │   │ Adapter│   │ Adapter│
│ UI09   │   │        │   │        │
└────────┘   └────────┘   └────────┘
    │
    ▼
┌─────────────────────────────────┐
│ HTML-Übersicht mit Farbcodierung  │
│ (OK=grün, WARN=gelb, FEHL=rot)  │
│ + Entscheidungsempfehlung         │
│ + Zulässige/blockierte Schritte   │
│ + Freeze-Grenzen-Hinweis          │
└─────────────────────────────────┘
```

## Eingaben

UI13 liest **ausschließlich** die Ausgaben der Module UI08–UI12:

| Modul | Commit | Erwartete Ausgaben |
|-------|--------|-------------------|
| UI08 | `fb92b31` | `UI08_BERICHT.{json,html,txt}` |
| UI08b | `4c7269e` | `UI08B_FEHLERPFAD_PRUEFUNG.{json,html,txt}` |
| UI08c | `d22ac18` | `UI08C_SANIERUNGSPLAN.{json,html,txt}` |
| UI09 | `ae2e947` | `UI09_PROFILFELDER.json`, `UI09_GRUNDSCHALTER.html` |
| UI10 | `39923fd` | `UI10_PROFIL_ADAPTER.{json,html,txt}` |
| UI11 | `6198591` | `UI11_REGISTER_ADAPTER.{json,html,txt}` |
| UI12 | `d78cb74` | `UI12_MASTER_ADAPTER.{json,html,txt}` |

## Entscheidungslogik

| Bedingung | Empfehlung | Zulässig | Blockiert |
|-----------|-----------|----------|-----------|
| Alle Module abgeschlossen, keine Blockaden | Freeze-Öffnung kann kontrolliert erwogen werden | Freeze-Öffnung planen, UI03–UI07b modifizieren | – |
| Adapter fehlen (UI10/UI11) | UI10 und UI11 zuerst ausführen | UI10 ausführen, UI11 ausführen, UI12 erneut ausführen | Freeze-Öffnung, Produktivfreigabe |
| Warnungen > 0, keine Blockaden | Technische Abnahme möglich, fachliche Prüfung empfohlen | Technische Abnahme UI08–UI12, Freeze-Öffnung planen | Produktivfreigabe |
| Kritische Blockaden > 0 | Nur Sanierungsmodule zulässig | UI08b, UI08c, UI09 prüfen | Freeze-Öffnung, Produktivfreigabe, UI03–UI07b modifizieren |

## Ausgaben

| Datei | Pfad |
|-------|------|
| HTML-Übersicht | `Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT.html` |
| JSON-Übersicht | `Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT.json` |
| Text-Bericht | `Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT_BERICHT.txt` |

## Lieferpflicht (AGENTS.md)

- [x] Config: `Config/ui13_abnahme_entscheidungsuebersicht_v1.json`
- [x] Python-Läufer: `Scripts/python_runner/ui13_abnahme_entscheidungsuebersicht.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui13_abnahme_entscheidungsuebersicht.py`
- [x] PowerShell-Starter: `Scripts/UI13_ABNAHME_ENTSCHEIDUNGSUEBERSICHT_AUTOLAUF.ps1`
- [x] Dokumentation: `Projektplanung/UI13_ABNAHME_ENTSCHEIDUNGSUEBERSICHT.md`
- [x] Testlauf: Erfolgreich
- [x] Bericht: `Windows_App/Logs/UI13_ENTSCHEIDUNGSUEBERSICHT_BERICHT.txt`

## Sperrregister

UI13 prüft vor dem Start das Sperrregister (`ALIN_Neustart_Core/01_Register/sperrregister.json`).
Bei Sperrung wird die Ausführung abgebrochen.

## Abhängigkeiten

| Modul | Zweck |
|-------|-------|
| UI08–UI12 | Ausgaben werden lesend konsumiert |

## Autor

ALIN System | Version 1.0.0 | Status: Entwurf | Demo-Modus

## Changelog

| Datum | Änderung |
|-------|----------|
| 2026-05-17 | Erstversion UI13 Abnahme- und Entscheidungsübersicht |
