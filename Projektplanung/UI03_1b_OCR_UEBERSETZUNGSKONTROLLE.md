# UI03-1b – OCR-/Übersetzungskontrolle der Mandantenakte

**Modul:** UI03-1b  
**Version:** 1.0.0  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen  
**CORE-11-konform:** Ja  

---

## Zweck

UI03-1b ist die Erweiterung von UI03-1 (Anwalts-Dreiansicht). Es prüft und dokumentiert den OCR-/Übersetzungsstatus anhand der bereinigten CORE-11-Register, bevor die Dreiansicht angezeigt wird.

Die Kontrolle zeigt:
- **Tesseract OCR**: freigegeben (offline, installiert)
- **Argos Translate**: gesperrt (keine vollständigen Sprachpaare vorhanden)
- **DEEPL API**: gesperrt (Cloud-Nutzung laut Richtlinie verboten)
- **Deutsche Arbeitsansicht**: nur Orientierungsübersetzung (nicht endgültig)

---

## Architektur

```
UI03_Mandantenakte/
  21_OCR_Uebersetzungskontrolle_UI03_1b/
    02_Status/UI03_1b_OCR_KONTROLLE_STATUS.html
    02_Status/UI03_1b_OCR_KONTROLLE_STATUS.json
    03_Berichte/UI03_1b_OCR_KONTROLLE_BERICHT.txt
    05_Fehler/UI03_1b_OCR_KONTROLLE_FEHLER.txt
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
| `UI03_1b_OCR_KONTROLLE_STATUS.html` | HTML-Status-Panel mit Dreiansicht-Schema |
| `UI03_1b_OCR_KONTROLLE_STATUS.json` | Maschinenlesbarer Status |
| `UI03_1b_OCR_KONTROLLE_BERICHT.txt` | Menschenlesbarer Bericht |
| `UI03_1b_OCR_KONTROLLE_FEHLER.txt` | Fehlerbericht |

---

## Register-Prüfung

### Tesseract OCR
- **Tool-ID:** `TESSERACT`
- **Status:** `freigegeben`
- **Grund:** Installiert, offline verfügbar

### Argos Translate
- **Tool-ID:** `ARGOS_TRANSLATE`
- **Status:** `gesperrt`
- **Grund:** Installationsstatus unbekannt, keine vollständigen Sprachpaare
- **Sprachpaare im Register:** 7 (ARGOS_DE_EN, ARGOS_EN_DE, ARGOS_DE_ES, ARGOS_DE_FR, ARGOS_DE_NL, ARGOS_DE_PL, ARGOS_DE_SV)
- **Vorhanden:** 0 (alle "unbekannt" oder "nein")

### DEEPL API
- **Ressourcen-ID:** `DEEPL_API`
- **Status:** `gesperrt`
- **Grund:** Cloud-Nutzung laut Richtlinie verboten (Offline-Betrieb)

---

## Sprachlogik

- Keine Hartverdrahtung auf sv/de
- Sprachen werden aus der Mandantenakte gelesen
- Argos-Paare werden dynamisch aus dem Ressourcenregister ermittelt
- Fallback: Keine Übersetzung (nur Orientierungsübersetzung aus UI02)

---

## Grenzen

| Grenze | Status |
|---|---|
| Keine Originaländerung | ✅ |
| Keine neue OCR | ✅ |
| Keine endgültige Übersetzung | ✅ |
| Keine DB-Änderung | ✅ |
| Kein Internet | ✅ |
| Keine Cloud | ✅ |
| Keine Registeränderung | ✅ |

---

## Tests

- py_compile: BESTANDEN
- Selbsttest: 16/16 BESTANDEN
- Hauptlauf: BESTANDEN (0 Fehler, 0 Warnungen)
- Prüfdatei: 30/30 BESTANDEN

---

## Dateien der Lieferpflicht

1. ✅ Python-Runner: `Scripts/python_runner/ui03_1b_ocr_uebersetzungskontrolle.py`
2. ✅ Prüfdatei: `Scripts/python_runner/check_ui03_1b_ocr_uebersetzungskontrolle.py`
3. ✅ PowerShell-Starter: `Scripts/UI03_1b_OCR_UEBERSETZUNGSKONTROLLE_AUTOLAUF.ps1`
4. ✅ Konfiguration: `Config/ui03_1b_ocr_uebersetzungskontrolle_v1.json`
5. ✅ Dokumentation: `Projektplanung/UI03_1b_OCR_UEBERSETZUNGSKONTROLLE.md`
6. ✅ Bericht: `Windows_App/Logs/UI03_1b_OCR_KONTROLLE_BERICHT.txt`

---

## Nächster Schritt

- UI03-2: Vollständige Dreiansicht mit echten Daten
- UI04c: Agentenaufträge vorbereiten
- UI05: Reguläre Übersetzung (wenn Argos-Paare verfügbar)
