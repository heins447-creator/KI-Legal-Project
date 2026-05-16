# UI03-1g – Kombinierte Gesamtansicht

## Zweck

Zusammenführendes Dashboard, das die Ergebnisse der Module **UI03-1b bis UI03-1f** auf einen Blick sichtbar macht. Keine Neuberechnung, keine Veränderung vorhandener Daten – reine Aggregation.

## Was angezeigt wird

1. **Gesamt-Status** – Oben: „ÜBERSETZUNG GEPARKT" oder „BEREIT FÜR WIEDERAUFNAHME"
2. **Modul-Karten** – Jeder der 5 Vorgänger als Karte mit Status (geladen / nicht gefunden)
3. **Übersetzungsauftrag** – Auftrags-ID, Parkgrund, Seiten-Statistik (freigegeben / Neu-OCR / ausgeschlossen / zurückgestellt / wartet)
4. **Argos-Status** – Lokale Modelle verfügbar? Wie viele Sprachpaare?
5. **Nächster zulässiger Schritt** – Kette der möglichen Aktionen bis zur Wiederaufnahme oder KM21b

## Architektur

```text
UI03-1b (OCR-Status)    ─┐
UI03-1c (Arbeitsplatz)   ─┤
UI03-1d (Freigabe)       ─┼→ UI03-1g liest nur → Dashboard-HTML + Aggregat-JSON
UI03-1e (Auftrag)        ─┤
UI03-1f (Geparkte)       ─┘
```

- UI03-1g schreibt in **eigenen Schreibbereich**: `Agentensteuerung\UI03_Mandantenakte\26_Gesamtansicht_UI03_1g\`
- Liest Status-JSONs aus den Schreibbereichen von 1b–1f
- Liest Tool-/Ressourcenregister für Argos-Status (nur lesend)

## Liefergegenstände

| Datei | Zweck |
|-------|-------|
| `Scripts/python_runner/ui03_1g_gesamtansicht.py` | Python-Läufer |
| `Scripts/python_runner/check_ui03_1g_gesamtansicht.py` | Prüfdatei (15 Checks) |
| `Scripts/UI03_1g_GESAMTANSICHT_AUTOLAUF.ps1` | PowerShell-Starter |
| `Config/ui03_1g_gesamtansicht_v1.json` | Konfiguration |
| `Projektplanung/UI03_1g_GESAMTANSICHT.md` | Diese Dokumentation |

## Grenzen

- ✓ Keine Originaländerung
- ✓ Keine neue OCR
- ✓ Keine echte Übersetzung (nur Anzeige)
- ✓ Keine DB-Änderung
- ✓ Kein Internet/Cloud
- ✓ Keine Registeränderung (nur lesend)
- ✓ **Keine Vorgänger-Module verändert** (nur lesend)

## Abhängigkeiten

- UI03-1b … UI03-1f müssen mindestens einmal ausgeführt worden sein (Status-JSONs)
- CORE-11-Register (toolregister.json, ressourcenregister.json)

## Nächster Schritt nach UI03-1g

- **KM21b** – Lokale Argos-Modelle bereitstellen (wenn Argos fehlt)
- Oder: Argos verfügbar → Wiederaufnahme der Übersetzung
