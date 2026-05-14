# KM20 – Quellen- und Fundstellenkonsolidierung — DOKUMENTATION

## Baustein
KM20 konsolidiert pro OCR-Seite sämtliche Quellbezüge, Fundstellen (KM14), Übersetzungseinheiten (KM15), Koordinaten, Unsicherheiten und die Rückbindungskette auf Vorläufermodule (KM12, KM12b, KM13, KM17, KM17c, KM19).

## Technik
- Sprache: Python 3.12
- Keine externen Bibliotheken ausser stdlib (json, csv, pathlib, hashlib)
- Rein lesend: keine Änderung an Originalen, OCR-Dateien, Datenbanken
- Keine Übersetzung, keine Internetnutzung, keine Rechtsbewertung

## Dateien

| Datei | Pfad |
|---|---|
| Konfiguration | Config/km20_quellen_fundstellen_konsolidierung_v1.json |
| Python-Läufer | Scripts/python_runner/km20_quellen_fundstellen_konsolidierung.py |
| Prüfdatei | Scripts/python_runner/km20_pruefung.py |
| PowerShell-Starter | Scripts/Run_KM20_Konsolidierung.ps1 |
| Dokumentation | Projektplanung/KM20_KONSOLIDIERUNG.md |

## Ausgaben (Bereich: Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung)

| Datei | Pfad |
|---|---|
| Status | 02_Status/KM20_STATUS.json |
| Bericht | 03_Berichte/KM20_BERICHT.txt |
| Fehler | 05_Fehler/KM20_FEHLER.txt |
| Master-Index JSON | 07_Manifest/KM20_MASTER_INDEX.json |
| Master-Index CSV | 07_Manifest/KM20_MASTER_INDEX.csv |
| Konsolidierung JSON | 08_Konsolidierung/KM20_KONSOLIDIERUNG.json |
| Konsolidierung CSV | 08_Konsolidierung/KM20_KONSOLIDIERUNG.csv |
| Unsicherheiten | 09_Unsicherheiten/KM20_UNSICHERHEITEN.json |
| Rückbindung | 10_Rueckbindung/KM20_RUECKBINDUNG.json |

## Ergebnisse

- 25 Seiten konsolidiert (24 echte + 1 Testdummy ORG-T)
- 4 Originale (3 real: ORG-970b..., ORG-9dd..., ORG-f69d... + ORG-T)
- 4.560 Fundstellen (KM14)
- 4.560 Übersetzungseinheiten (KM15)
- 27 Unsicherheiten (niedrige OCR-Konfidenz, fehlende Sprachbestimmung)
- Rückbindungstiefe max: 7 Module (KM12, KM12b, KM13, KM17, KM17c, KM19, KM14, KM15)
- Alle Seiten haben Koordinaten-BBox

## Grenzen
- Keine Originaländerung
- Keine OCR, Übersetzung, DB-Änderung
- Kein Internet, keine Installation
- Keine echten Mandantendaten verarbeitet
