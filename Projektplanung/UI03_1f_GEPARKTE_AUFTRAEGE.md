# UI03-1f – Geparkte Übersetzungsaufträge verwalten

**Modul:** UI03-1f  
**Version:** 1.0.0  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen  
**CORE-11-konform:** Ja  

---

## Zweck

UI03-1f ist das Verwaltungs-Interface für alle geparkten Übersetzungsaufträge im Projekt. Es zeigt:

- **Geparkte Aufträge**: Liste aller vorbereiteten, aber nicht gestarteten Übersetzungsaufträge
- **Parkgrund**: Warum jeder Auftrag geparkt ist (Argos fehlt, etc.)
- **Fehlende Modelle**: Argos-Sprachpaare, die fehlen
- **Betroffene Seiten/Dokumente**: Statistik pro Auftrag
- **Wiederaufnahme**: Vorbereitung, sobald Argos lokal freigegeben ist

### Status

```text
WARTET AUF LOKALE MODELLE
```

---

## Architektur

```
UI03_Mandantenakte/
  25_Geparkte_Auftraege_UI03_1f/
    02_Status/UI03_1f_GEPARKTE_AUFTRAEGE.html
    02_Status/UI03_1f_GEPARKTE_AUFTRAEGE.json
    03_Berichte/UI03_1f_GEPARKTE_AUFTRAEGE_BERICHT.txt
    05_Fehler/UI03_1f_GEPARKTE_AUFTRAEGE_FEHLER.txt
    07_Manifest/
```

---

## Eingaben

| Quelle | Datei | Zweck |
|---|---|---|
| UI03-1e | `Agentensteuerung/UI03_Mandantenakte/24_Uebergabe_Freigabe_UI03_1e/02_Status/UI03_1e_UEBERGABE_FREIGABE.json` | Geparkte Aufträge |
| CORE-11 | `ALIN_Neustart_Core/01_Register/toolregister.json` | Argos-Status |
| CORE-11 | `ALIN_Neustart_Core/01_Register/ressourcenregister.json` | Argos-Paare |

---

## Ausgaben

| Datei | Zweck |
|---|---|
| `UI03_1f_GEPARKTE_AUFTRAEGE.html` | HTML-Verwaltungs-Interface |
| `UI03_1f_GEPARKTE_AUFTRAEGE.json` | Gesamtstatus |
| `UI03_1f_GEPARKTE_AUFTRAEGE_BERICHT.txt` | Menschenlesbarer Bericht |
| `UI03_1f_GEPARKTE_AUFTRAEGE_FEHLER.txt` | Fehlerbericht |

---

## Auftragssuche

UI03-1f durchsucht das Projekt nach geparkten Aufträgen:

- **Primär**: UI03-1e Schreibbereich (`24_Uebergabe_Freigabe_UI03_1e/`)
- **Kriterium**: `status == "vorbereitet"`
- **Gesammelt**: Auftrags-ID, Akten-ID, Parkgrund, Seiten-Statistik

---

## HTML-Struktur

### Argos-Status-Banner
- Gelb: "ARGOS NICHT BEREIT – Keine Sprachpaare vorhanden"
- Grün (falls verfügbar): "ARGOS BEREIT – Wiederaufnahme möglich"

### Gesamtübersicht
- Geparkte Aufträge
- Seiten gesamt
- Freigegeben
- Argos-Paare

### Pro Auftrag (Karte)
- Auftrags-ID, Akten-ID, Erstellungszeit, Quelle
- Parkgrund-Box (hervorgehoben)
- Mini-Statistik: Seiten, Freigegeben, Neu-OCR, Ausgeschlossen, Zurückgestellt, Wartet
- Aktionen: Wiederaufnahme vorbereiten (disabled wenn Argos fehlt), Details

---

## Grenzen

| Grenze | Status |
|---|---|
| Keine Originaländerung | ✅ |
| Keine neue OCR | ✅ |
| Keine echte Übersetzung (nur vorbereiten/parken) | ✅ |
| Keine DB-Änderung | ✅ |
| Kein Internet | ✅ |
| Keine Cloud | ✅ |
| Keine Registeränderung (nur lesend) | ✅ |

---

## Tests

- py_compile: BESTANDEN
- Selbsttest: 9/9 BESTANDEN
- Hauptlauf: BESTANDEN
- Prüfdatei: 20/20 BESTANDEN

---

## Dateien der Lieferpflicht

1. ✅ Python-Runner: `Scripts/python_runner/ui03_1f_geparkte_auftraege.py`
2. ✅ Prüfdatei: `Scripts/python_runner/check_ui03_1f_geparkte_auftraege.py`
3. ✅ PowerShell-Starter: `Scripts/UI03_1f_GEPARKTE_AUFTRAEGE_AUTOLAUF.ps1`
4. ✅ Konfiguration: `Config/ui03_1f_geparkte_auftraege_v1.json`
5. ✅ Dokumentation: `Projektplanung/UI03_1f_GEPARKTE_AUFTRAEGE.md`
6. ✅ Bericht: `Windows_App/Logs/UI03_1f_GEPARKTE_AUFTRAEGE_BERICHT.txt`

---

## Nächster Schritt

- KM21b: Lokale Argos-Modelle bereitstellen (wenn `.argosmodel`-Dateien vorliegen oder Download freigegeben)
- UI03-2: Vollständige Dreiansicht mit freigegebenen Seiten (nach Argos-Freigabe)
