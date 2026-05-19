# STUFE-020: Datenschutz und Mandatsgeheimnis

## Ziel

Technische und organisatorische Grundschicht für:
- Mandatsgeheimnis
- Datenschutz
- Zugriff nach Rollen
- Protokollierung
- Datenminimierung
- Zweckbindung
- Schutz echter Daten
- Sperre externer Dienste

## Hintergrund

Dieses Modul ist keine Produktiv-Datenschutzfreigabe, sondern die Basisregelung, die alle nachfolgenden Module bindend einhalten müssen. Es definiert Markierungen, die an Daten und Dokumenten angebracht werden, um deren Schutzstufe maschinell erkennbar zu machen.

## Lieferpflichten

| # | Artefakt | Pfad | Status |
|---|----------|------|--------|
| 1 | Python-Läufer | `Scripts/python_runner/core20_datenschutz_mandatsgeheimnis.py` | erstellt |
| 2 | Prüfdatei | `Scripts/python_runner/check_core20_datenschutz_mandatsgeheimnis.py` | erstellt |
| 3 | PowerShell-Starter | `Scripts/CORE20_DATENSCHUTZ_MANDATSGEHEIMNIS_AUTOLAUF.ps1` | erstellt |
| 4 | Konfiguration | `Config/core20_datenschutz_mandatsgeheimnis_v1.json` | erstellt |
| 5 | Dokumentation | `Projektplanung/STUFE-020_Datenschutz_Mandatsgeheimnis.md` | diese Datei |
| 6 | Mandatsgeheimnis-Regeln | `ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/MANDATSGEHEIMNIS_REGELN.md` | vorhanden |
| 7 | Exportregeln | `ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/EXPORTREGELN.md` | vorhanden |
| 8 | Datenschutz-Schema | `ALIN_Neustart_Core/20_Datenschutz_Mandatsgeheimnis/DATENSCHUTZ_MARKIERUNGEN.schema.json` | vorhanden |

## Regelwerke

### Mandatsgeheimnis-Regeln
- Mandantenbezogene Daten nur lokal verarbeiten
- Keine Weitergabe an externe Modelle ohne Freigabe
- Keine Cloud-Speicherung ohne Freigabe
- Export nur mit Freigabe und Protokoll
- Löschung nach Mandatsende + 10 Jahre

### Exportregeln
- Export nur mit Administrator-Freigabe
- Protokollierung: Wer, wann, was
- Kein Export von Originaldokumenten ohne Anonymisierung
- Kein Export von personenbezogenen Daten ohne Freigabe
- Erlaubt: Anonymisierte Statistiken, Protokolle (ohne Daten), Konfigurationen

### Datenschutz-Markierungen

| Markierung | Bedeutung |
|------------|-----------|
| `mandatsbezogen` | Daten gehören zu einem Mandat |
| `personenbezogen` | Daten enthalten personenbezogene Informationen |
| `besonders_schutzbeduerftig` | Besondere Schutzbedürftigkeit (z.B. Minderjährige) |
| `nur_lokal` | Darf nicht das System verlassen |
| `nicht_exportieren` | Export gesperrt |
| `nicht_an_externe_modelle` | Keine Weitergabe an externe KI-Modelle |
| `cloud_verboten` | Cloud-Speicherung untersagt |

## Tests

- Schema ist gültiges JSON
- Schema enthält alle Pflichtfelder: `schema_version`, `markierung_id`, `objekt_id`, `markierungen`
- Schema enthält alle sieben Markierungen im Enum
- Markdown-Dateien sind strukturiert (Überschriften vorhanden)
- Bericht wird unter `ALIN_Neustart_Core/Reports/CORE20_DATENSCHUTZ_MANDATSGEHEIMNIS_BERICHT.txt` geschrieben

## Abhängigkeiten

- STUFE-019 (Rechte und Rollen) muss abgeschlossen sein

## Nächste Stufe

- STUFE-024 (Autonomer Entwicklungsmanager) oder STUFE-025 (Programmierbare Gesamt-Roadmap)
