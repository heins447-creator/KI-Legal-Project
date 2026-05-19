# UI14 – Ausführungs- und Nachlaufzentrale UI08–UI13

## Zweck

UI14 ist **keine neue Fachlogik**, sondern eine **saubere Ausführungs- und Nachlaufzentrale**, die alle Module UI08 bis UI13 in der korrekten Reihenfolge ausführt, erwartbare Warnungen von echten Fehlern trennt und abschließend UI13 als zentrale HTML-Entscheidungsseite öffnet.

Damit werden die 20 erwarteten UI13-Warnungen aus fehlenden Vorläufer-Ausgaben bereinigt, ohne den Freeze UI03–UI07b anzutasten.

## Ausführungsreihenfolge

| Schritt | Modul | Abhängigkeiten | Zweck |
|---------|-------|---------------|-------|
| 1 | UI08 | – | Posteingang Importstrecke |
| 2 | UI08b | UI08 | Fehlerpfadprüfung |
| 3 | UI08c | UI08, UI08b | Sanierungsplan |
| 4 | UI09 | – | Grundschalter und Profilfelder |
| 5 | UI10 | UI09 | Profil-Leseadapter |
| 6 | UI11 | – | Register-Leseadapter |
| 7 | UI12 | UI10, UI11 | Master-Adapter |
| 8 | UI13 | UI08–UI12 | Entscheidungsübersicht |

## Fehlerbehandlung

| Situation | Verhalten |
|-----------|-----------|
| Echter Fehler (Exitcode ≠ 0, nicht erwartet) | Abbruch mit Bericht |
| Erwartete Warnung (Demo-Modus, fehlende Eingaben) | Fortfahren mit Protokoll |
| Timeout (> 300s pro Schritt) | Abbruch mit Fehler |
| Max. Warnungen (> 50) überschritten | Abbruch |

## Nachlauf

Nach erfolgreicher Ausführung aller 8 Schritte:

1. Bericht erzeugen: `UI14_NACHLAUFZENTRALE_BERICHT.txt`
2. Zusammenfassung JSON: `UI14_ZUSAMMENFASSUNG.json`
3. **UI13-HTML im Browser öffnen**: `UI13_ENTSCHEIDUNGSUEBERSICHT.html`

## Freeze-Kompatibilität

| Kriterium | Wert |
|-----------|------|
| Berührt UI03–UI07b | **Nein** |
| Führt nur UI08–UI13 aus | **Ja** |
| Neue Dateien | **Ja** (nur UI14-Ausgaben) |
| produktiv_freigegeben | **false** |
| nur_musterdaten | **true** |
| echte_daten_erlaubt | **false** |

## Lieferpflicht (AGENTS.md)

- [x] Config: `Config/ui14_ausfuehrungs_nachlaufzentrale_v1.json`
- [x] Python-Läufer: `Scripts/python_runner/ui14_ausfuehrungs_nachlaufzentrale.py`
- [x] Prüfdatei: `Scripts/python_runner/check_ui14_ausfuehrungs_nachlaufzentrale.py`
- [x] PowerShell-Starter: `Scripts/UI14_AUSFUEHRUNGS_NACHLAUFZENTRALE_AUTOLAUF.ps1`
- [x] Dokumentation: `Projektplanung/UI14_AUSFUEHRUNGS_NACHLAUFZENTRALE.md`
- [x] Testlauf: Erfolgreich
- [x] Bericht: `Windows_App/Logs/UI14_NACHLAUFZENTRALE_BERICHT.txt`

## Sperrregister

UI14 prüft vor dem Start das Sperrregister (`ALIN_Neustart_Core/01_Register/sperrregister.json`).
Bei Sperrung wird die Ausführung abgebrochen.

## Abhängigkeiten

| Modul | Zweck |
|-------|-------|
| UI08–UI13 | Werden in Reihenfolge ausgeführt |

## Autor

ALIN System | Version 1.0.0 | Status: Entwurf | Demo-Modus

## Changelog

| Datum | Änderung |
|-------|----------|
| 2026-05-17 | Erstversion UI14 Ausführungs- und Nachlaufzentrale |
