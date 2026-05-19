# UI03-1d – OCR-Prüf- und Freigabeablauf vor Übersetzung

**Modul:** UI03-1d  
**Version:** 1.0.0  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen  
**CORE-11-konform:** Ja  

---

## Zweck

UI03-1d ist der OCR-Prüf- und Freigabeablauf vor Übersetzung. Er ermöglicht dem Anwalt oder Mitarbeiter, jede Seite der Mandantenakte einzeln zu prüfen und eine Freigabe-Entscheidung zu treffen.

### Freigabe-Optionen pro Seite

1. **OCR qualitativ ausreichend – freigegeben für Übersetzung**
   - Seite wird für die spätere Übersetzung markiert
   
2. **OCR mangelhaft – Neu-OCR erforderlich**
   - Seite braucht bessere OCR (z. B. anderes Sprachpaket)
   
3. **Seite nicht übersetzungsrelevant – ausschließen**
   - Seite wird von der Übersetzung ausgeschlossen
   
4. **Anwalt prüft – Freigabe zurückstellen**
   - Entscheidung wird vertagt

### Pro Seite
- OCR-Text-Vorschau (400 Zeichen)
- Orientierungsübersetzung-Vorschau (400 Zeichen)
- Freitext-Anmerkungen

---

## Architektur

```
UI03_Mandantenakte/
  23_OCR_Freigabeablauf_UI03_1d/
    02_Status/UI03_1d_OCR_FREIGABEABLAUF.html
    02_Status/UI03_1d_OCR_FREIGABEABLAUF.json
    03_Berichte/UI03_1d_OCR_FREIGABEABLAUF_BERICHT.txt
    05_Fehler/UI03_1d_OCR_FREIGABEABLAUF_FEHLER.txt
    07_Manifest/
```

---

## Eingaben

| Quelle | Datei | Zweck |
|---|---|---|
| UI03-0 | `Agentensteuerung/UI03_Mandantenakte/10_Mandantenakte/Mandantenakte.json` | Akte mit Dokumenten und Seiten |
| CORE-11 | `ALIN_Neustart_Core/01_Register/toolregister.json` | Tesseract-Status (optional) |

---

## Ausgaben

| Datei | Zweck |
|---|---|
| `UI03_1d_OCR_FREIGABEABLAUF.html` | HTML-Freigabe-Interface mit allen Seiten |
| `UI03_1d_OCR_FREIGABEABLAUF.json` | Maschinenlesbarer Status |
| `UI03_1d_OCR_FREIGABEABLAUF_BERICHT.txt` | Menschenlesbarer Bericht |
| `UI03_1d_OCR_FREIGABEABLAUF_FEHLER.txt` | Fehlerbericht |

---

## HTML-Struktur

### Gesamtübersicht
- Anzahl Dokumente
- Anzahl Seiten
- Freigegeben (Platzhalter für spätere Dynamik)
- Zurückgestellt (Platzhalter)

### Pro Seite (Karte)
- Dokument-Metadaten (Titel, Sprache, Rechtsgebiet)
- OCR-Status und Übersetzungs-Status
- Zweiseitige Vorschau: OCR-Text / Orientierungsübersetzung
- 4 Radio-Buttons für Freigabe-Entscheidung
- Textarea für Anmerkungen

---

## Grenzen

| Grenze | Status |
|---|---|
| Keine Originaländerung | ✅ |
| Keine neue OCR (nur Freigabe-Markierung) | ✅ |
| Keine endgültige Übersetzung | ✅ |
| Keine DB-Änderung | ✅ |
| Kein Internet | ✅ |
| Keine Cloud | ✅ |
| Keine Registeränderung (nur lesend) | ✅ |

---

## Tests

- py_compile: BESTANDEN
- Selbsttest: 13/13 BESTANDEN
- Hauptlauf: BESTANDEN
- Prüfdatei: 20/20 BESTANDEN

---

## Dateien der Lieferpflicht

1. ✅ Python-Runner: `Scripts/python_runner/ui03_1d_ocr_freigabeablauf.py`
2. ✅ Prüfdatei: `Scripts/python_runner/check_ui03_1d_ocr_freigabeablauf.py`
3. ✅ PowerShell-Starter: `Scripts/UI03_1d_OCR_FREIGABEABLAUF_AUTOLAUF.ps1`
4. ✅ Konfiguration: `Config/ui03_1d_ocr_freigabeablauf_v1.json`
5. ✅ Dokumentation: `Projektplanung/UI03_1d_OCR_FREIGABEABLAUF.md`
6. ✅ Bericht: `Windows_App/Logs/UI03_1d_OCR_FREIGABEABLAUF_BERICHT.txt`

---

## Nächster Schritt

- UI03-2: Vollständige Dreiansicht mit echten Daten und Freigabe-Status
- UI05: Reguläre Übersetzung (wenn Argos-Paare verfügbar und Seiten freigegeben)
