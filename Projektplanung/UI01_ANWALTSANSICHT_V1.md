# UI01 - Anwaltliche Dokumentenvorlage V1

## Status

| Merkmal | Wert |
|---------|------|
| Modul | UI01 |
| Version | 1.0.0 |
| Zweck | Erste sichtbare anwaltliche Arbeitsansicht im Browser |
| Ausgewaehltes Dokument | ORG-970b270eb1e8-00163 (3 Seiten) |
| Arbeitsvertrag erkannt | unsicher |
| Originalansicht | verweist auf KM12-Pfade (nicht direkt im Browser darstellbar) |
| OCR verfuegbar | JA (Fundstellen aus KM14 referenziert) |
| Uebersetzung aktiv | NEIN (KM15 gesperrt) |

## Aufbau

- Linkes Panel: Original-/Arbeitsabbildung mit Seiten-Navigation
- Rechtes Panel: OCR-Textstellen und Fundstellen
- Merkmalspanel: Automatisch extrahierte Dokumentmerkmale (arbeitsvertrag, Parteien, Daten, Aktenzeichen, Sprache)
- Notizpanel: Anwaltliche Notiz, Arbeitsauftrag an Sekretariat
- Mikrofon-Buttons: Web Speech API (lokal, kein Clouddienst)
- Entscheidungspanel: Mandat annehmen/ablehnen/zurueckstellen/zuordnen + Begruendung

## Browseransicht

Pfad: Agentensteuerung\UI01_Anwaltsansicht_V1\10_Browseransicht\index.html

Im Browser oeffnen (Doppelklick oder PowerShell):
  Start-Process "I:\KI_Legal_Project\Agentensteuerung\UI01_Anwaltsansicht_V1\10_Browseransicht\index.html"

## Dateien

| Datei | Pfad |
|-------|------|
| Runner | Scripts\python_runner\ui01_anwaltsansicht_v1.py |
| Pruefdatei | Scripts\python_runner\check_ui01_anwaltsansicht_v1.py |
| Autolauf | Scripts\UI01_ANWALTSANSICHT_AUTOLAUF.ps1 |
| Config | Config\ui01_anwaltsansicht_v1.json |
| HTML | Agentensteuerung\UI01_Anwaltsansicht_V1\10_Browseransicht\index.html |
| CSS | Agentensteuerung\UI01_Anwaltsansicht_V1\10_Browseransicht\ui01.css |
| JS | Agentensteuerung\UI01_Anwaltsansicht_V1\10_Browseransicht\ui01.js |
| Status | Agentensteuerung\UI01_Anwaltsansicht_V1\02_Status\UI01_STATUS.json |
| ViewData | Agentensteuerung\UI01_Anwaltsansicht_V1\08_ViewData\UI01_DOKUMENT_VIEWDATA.json |
| Notizen | Agentensteuerung\UI01_Anwaltsansicht_V1\09_Notizen\UI01_NOTIZEN_TEMPLATE.json |
| Entscheidung | Agentensteuerung\UI01_Anwaltsansicht_V1\11_Entscheidung\UI01_ENTSCHEIDUNG_TEMPLATE.json |

## Grenzen eingehalten

- Keine Originaldateiaenderung
- Keine neue OCR
- Keine Uebersetzungserfindung
- Keine DB-Aenderung
- Keine Internetnutzung
- Keine Cloud
- Keine Rechtsberatung

## Naechster Auftrag

UI01 im Browser pruefen, Notizfelder testen, Layout bewerten.
Originalbilder koennen ueber file://-Links eingebunden werden, wenn KM12-Bilder auffindbar sind.
