# UI03-1e – Übergabe der OCR-Freigabeentscheidung an die Übersetzungsstrecke

**Modul:** UI03-1e  
**Version:** 1.0.0  
**Datum:** 2026-05-16  
**Status:** Abgeschlossen  
**CORE-11-konform:** Ja  

---

## Zweck

UI03-1e übernimmt die OCR-Freigabeentscheidung (aus UI03-1d) und bereitet die Übersetzungsstrecke vor. Es kategorisiert alle Seiten der Mandantenakte und erzeugt einen strukturierten Übersetzungsauftrag.

### Kategorien

| Kategorie | Bedeutung | Übersetzung |
|---|---|---|
| `freigegeben` | OCR qualitativ ausreichend | ✓ Wird übersetzt |
| `neu_ocr` | OCR mangelhaft | ✗ Neu-OCR erforderlich |
| `ausgeschlossen` | Nicht übersetzungsrelevant | ✗ Ausgeschlossen |
| `zurueckgestellt` | Anwalt prüft später | ✗ Vertagt |
| `wartet` | Noch keine Entscheidung | ✗ Wartet |

### Park-Status

Der Auftrag bleibt **geparkt**, solange Argos-Modelle nicht verfügbar sind. Keine echte Übersetzung wird gestartet.

---

## Architektur

```
UI03_Mandantenakte/
  24_Uebergabe_Freigabe_UI03_1e/
    02_Status/UI03_1e_UEBERGABE_FREIGABE.html
    02_Status/UI03_1e_UEBERGABE_FREIGABE.json
    02_Status/UI03_1e_UEBERGABE_FREIGABE_STATUS.json
    03_Berichte/UI03_1e_UEBERGABE_FREIGABE_BERICHT.txt
    05_Fehler/UI03_1e_UEBERGABE_FREIGABE_FEHLER.txt
    07_Manifest/
```

---

## Eingaben

| Quelle | Datei | Zweck |
|---|---|---|
| UI03-0 | `Agentensteuerung/UI03_Mandantenakte/10_Mandantenakte/Mandantenakte.json` | Akte mit Dokumenten und Seiten |
| CORE-11 | `ALIN_Neustart_Core/01_Register/toolregister.json` | Argos-Status |
| CORE-11 | `ALIN_Neustart_Core/01_Register/ressourcenregister.json` | Argos-Paare |

---

## Ausgaben

| Datei | Zweck |
|---|---|
| `UI03_1e_UEBERGABE_FREIGABE.html` | HTML-Interface mit Auftragszusammensetzung |
| `UI03_1e_UEBERGABE_FREIGABE.json` | Übersetzungsauftrag (maschinenlesbar) |
| `UI03_1e_UEBERGABE_FREIGABE_STATUS.json` | Gesamtstatus |
| `UI03_1e_UEBERGABE_FREIGABE_BERICHT.txt` | Menschenlesbarer Bericht |
| `UI03_1e_UEBERGABE_FREIGABE_FEHLER.txt` | Fehlerbericht |

---

## Initiale Kategorisierung

Die initiale Kategorie wird aus den existierenden Status-Werten der Seite abgeleitet:

- `ocr_verwertbarkeit_status` = "Türschwelle – nicht schriftsatzfähig" → `neu_ocr`
- `ocr_verwertbarkeit_status` = "schriftsatzfähig" → `freigegeben`
- `uebersetzung_status` = "Türschwelle – Orientierungsübersetzung" → `zurueckgestellt`
- Sonst → `wartet`

---

## Übersetzungsauftrag-JSON

```json
{
  "auftrag_id": "UA_Akte-..._20260516...",
  "akten_id": "Akte-20260515_011502",
  "zeitpunkt_erstellung": "2026-05-16T...",
  "status": "vorbereitet",
  "parkgrund": "Argos-Modelle nicht verfügbar – keine echte Übersetzung gestartet",
  "seiten": [
    {
      "seiten_id": "ORG-..._S0001",
      "dokument_id": "ORG-...",
      "seite_nummer": 1,
      "sprache": "Schwedisch",
      "ocr_text_vorschau": "...",
      "kategorie": "freigegeben",
      "urspruenglicher_status": {
        "ocr_verwertbarkeit": "Türschwelle – nicht schriftsatzfähig",
        "uebersetzung": "Türschwelle – Orientierungsübersetzung"
      },
      "anmerkung": ""
    }
  ]
}
```

---

## HTML-Struktur

### Park-Banner
- Gelb: "AUFTRAG VORBEREITET – GEPARKT: Argos-Modelle nicht verfügbar"
- Grün (falls Argos verfügbar): "Auftrag bereit – Übersetzung kann starten"

### Statistik
- Pro Kategorie: Anzahl Seiten als Zählbox

### Pro Seite (Karte)
- Dokument-Metadaten und aktuelle Kategorie-Badge
- Ursprünglicher OCR-Status und Übersetzungs-Status
- OCR-Text-Vorschau (200 Zeichen)
- 5 Radio-Buttons für Kategorie-Änderung
- Freitext-Anmerkung

---

## Grenzen

| Grenze | Status |
|---|---|
| Keine Originaländerung | ✅ |
| Keine neue OCR | ✅ |
| Keine echte Übersetzung (geparkt) | ✅ |
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

1. ✅ Python-Runner: `Scripts/python_runner/ui03_1e_uebergabe_freigabe.py`
2. ✅ Prüfdatei: `Scripts/python_runner/check_ui03_1e_uebergabe_freigabe.py`
3. ✅ PowerShell-Starter: `Scripts/UI03_1e_UEBERGABE_FREIGABE_AUTOLAUF.ps1`
4. ✅ Konfiguration: `Config/ui03_1e_uebergabe_freigabe_v1.json`
5. ✅ Dokumentation: `Projektplanung/UI03_1e_UEBERGABE_FREIGABE.md`
6. ✅ Bericht: `Windows_App/Logs/UI03_1e_UEBERGABE_FREIGABE_BERICHT.txt`

---

## Nächster Schritt

- KM21b: Lokale Argos-Modelle bereitstellen (wenn freigegeben)
- UI03-1f: Übersetzungsauftrag parken bis Modelle verfügbar
- UI03-2: Vollständige Dreiansicht mit freigegebenen Seiten
