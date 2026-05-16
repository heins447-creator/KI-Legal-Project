# UI03-1c – Übersetzungsarbeitsplatz bei fehlender lokaler Übersetzung

**Modul:** UI03-1c  
**Version:** 1.0.0  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen  
**CORE-11-konform:** Ja  

---

## Zweck

UI03-1c ist der Übersetzungsarbeitsplatz für die Mandantenakte. Er zeigt eine Dreiansicht mit OCR-Text als Arbeitsbasis, wenn keine vollständige Übersetzung verfügbar ist. Der Arbeitsplatz ermöglicht:

- **Dreiansicht**: Original / OCR-Text / Deutsche Arbeitsansicht
- **Folgeaufträge**: Checkboxes/Chips für standardisierte Nachbearbeitung
- **Sonstiges-Freitext**: Freie Eingabe weiterer Anmerkungen
- **Multilingual**: Keine Hartverdrahtung auf sv/de – Sprachen dynamisch aus Akte

---

## Architektur

```
UI03_Mandantenakte/
  22_Uebersetzungsarbeitsplatz_UI03_1c/
    02_Status/UI03_1c_UEBERSETZUNGSARBEITSPLATZ.html
    02_Status/UI03_1c_UEBERSETZUNGSARBEITSPLATZ.json
    03_Berichte/UI03_1c_UEBERSETZUNGSARBEITSPLATZ_BERICHT.txt
    05_Fehler/UI03_1c_UEBERSETZUNGSARBEITSPLATZ_FEHLER.txt
    07_Manifest/
```

---

## Eingaben

| Quelle | Datei | Zweck |
|---|---|---|
| CORE-11 | `ALIN_Neustart_Core/01_Register/toolregister.json` | Tool-Status (Tesseract, Argos) |
| CORE-11 | `ALIN_Neustart_Core/01_Register/ressourcenregister.json` | Ressourcen-Status (DEEPL, Argos-Paare) |
| CORE-11 | `ALIN_Neustart_Core/01_Register/schnittstellenregister.json` | Schnittstellen-Status |
| CORE-11 | `ALIN_Neustart_Core/01_Register/modulregister.json` | Modul-Status |
| UI03-0 | `Agentensteuerung/UI03_Mandantenakte/10_Mandantenakte/Mandantenakte.json` | Akte mit Dokumenten |

---

## Ausgaben

| Datei | Zweck |
|---|---|
| `UI03_1c_UEBERSETZUNGSARBEITSPLATZ.html` | HTML-Arbeitsplatz mit Dreiansicht, Folgeaufträgen, Status |
| `UI03_1c_UEBERSETZUNGSARBEITSPLATZ.json` | Maschinenlesbarer Status |
| `UI03_1c_UEBERSETZUNGSARBEITSPLATZ_BERICHT.txt` | Menschenlesbarer Bericht |
| `UI03_1c_UEBERSETZUNGSARBEITSPLATZ_FEHLER.txt` | Fehlerbericht |

---

## Funktionale Anforderungen

### 1. Dreiansicht mit OCR als Basis
- Wenn keine Übersetzung verfügbar: OCR-Text wird als Arbeitsbasis markiert
- Wenn Übersetzung verfügbar: Deutsche Arbeitsansicht zeigt Übersetzung
- Original-Spalte ist immer nur zur Ansicht (nicht veränderbar)

### 2. Folgeaufträge
Standard-Folgeaufträge als Checkboxes/Chips:
- Argos-Sprachpaar nachladen
- Tesseract-Sprachpaket prüfen
- Manuelle Übersetzung beauftragen
- Dokument an Sekretariat zurückgeben
- Anwalt um Entscheidung bitten
- OCR-Qualität verbessern

### 3. Sonstiges-Freitext
- Textarea für freie Eingabe weiterer Anmerkungen
- Platzhalter-Text: "Weitere Anmerkungen oder Aufträge hier eingeben..."

### 4. Status-Banner
- Dynamische Banner je nach Verfügbarkeit:
  - Grün: Übersetzung verfügbar
  - Gelb: OCR als Basis (keine Übersetzung)
  - Rot: Weder OCR noch Übersetzung verfügbar

---

## Register-Prüfung

### Tesseract OCR
- **Tool-ID:** `TESSERACT`
- **Status:** `freigegeben`
- **Grund:** Installiert, offline verfügbar

### Argos Translate
- **Tool-ID:** `ARGOS_TRANSLATE`
- **Status:** `gesperrt` oder `teilweise`
- **Grund:** Keine oder unvollständige Sprachpaare

### DEEPL API
- **Ressourcen-ID:** `DEEPL_API`
- **Status:** `gesperrt`
- **Grund:** Cloud-Nutzung laut Richtlinie verboten

---

## Sprachlogik

- Keine Hartverdrahtung auf sv/de
- Sprachen werden aus der Mandantenakte gelesen
- Argos-Paare werden dynamisch aus dem Ressourcenregister ermittelt
- Prüfung: Ist für Akten-Sprache → Deutsch ein Argos-Paar vorhanden?
- Fallback: OCR-Text als Arbeitsbasis

---

## Grenzen

| Grenze | Status |
|---|---|
| Keine Originaländerung | ✅ |
| Keine neue OCR (nur vorhandene anzeigen) | ✅ |
| Keine endgültige Übersetzung | ✅ |
| Keine DB-Änderung | ✅ |
| Kein Internet | ✅ |
| Keine Cloud | ✅ |
| Keine Registeränderung (nur lesend) | ✅ |

---

## Tests

- py_compile: BESTANDEN
- Selbsttest: 17/17 BESTANDEN
- Hauptlauf: BESTANDEN
- Prüfdatei: 21/21 BESTANDEN

---

## Dateien der Lieferpflicht

1. ✅ Python-Runner: `Scripts/python_runner/ui03_1c_uebersetzungsarbeitsplatz.py`
2. ✅ Prüfdatei: `Scripts/python_runner/check_ui03_1c_uebersetzungsarbeitsplatz.py`
3. ✅ PowerShell-Starter: `Scripts/UI03_1c_UEBERSETZUNGSARBEITSPLATZ_AUTOLAUF.ps1`
4. ✅ Konfiguration: `Config/ui03_1c_uebersetzungsarbeitsplatz_v1.json`
5. ✅ Dokumentation: `Projektplanung/UI03_1c_UEBERSETZUNGSARBEITSPLATZ.md`
6. ✅ Bericht: `Windows_App/Logs/UI03_1c_UEBERSETZUNGSARBEITSPLATZ_BERICHT.txt`

---

## Nächster Schritt

- UI03-2: Vollständige Dreiansicht mit echten Daten
- UI04c: Agentenaufträge vorbereiten
- UI05: Reguläre Übersetzung (wenn Argos-Paare verfügbar)
