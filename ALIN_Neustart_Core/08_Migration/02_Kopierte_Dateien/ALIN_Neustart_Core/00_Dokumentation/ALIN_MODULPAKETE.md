# ALIN Modulpakete

## Übersicht

ALIN ist in Pakete gegliedert. Jedes Paket enthält verwandte Module. Jedes Modul ist im Modulregister eingetragen.

## Pakete

### Paket 1: Eingang und Sicherheit
- Posteingang / Briefkasten
- Sicherheitsgate
- Sprachkontext-Gate
- Vorzimmer

### Paket 2: Weiche und Entscheidung
- Weiche (Routing)
- Bestandsabgleich
- Neumandat-Prüfung
- Verwaltungspost-Erkennung

### Paket 3: OCR und Übersetzung
- Originalabbildung (KM12)
- OCR-Pipeline (KM13)
- Fundstellenstruktur (KM14)
- Arbeitsübersetzung (KM15)
- Sprachrouting (KM16–KM17)
- OCR-Ergebnisdiagnose (KM18)
- Gesamtkette synchronisieren (KM19)
- Konsolidierung (KM20)
- Übersetzungsumgebung (KM21)

### Paket 4: Anwaltsansicht und Rücklauf
- Anwaltsansicht (UI01)
- Türschwelle (UI02)
- Mandantenakte (UI03)
- Rücklauf (UI04)

### Paket 5: Quellen und Skills
- Quellenbetreuer
- Quellenkandidaten
- Agenten-Kontext-Skill-Register
- Agentenbearbeitung
- Dokumentart erkennen
- Sprache übersetzen
- Sachverhaltsbezug

### Paket 6: System und Infrastruktur
- ALIN-Core (Grundmodell)
- Healthcheck
- Audit-Protokoll
- Toolbibliothek
- Lizenzregister
- Update-Überwachung
- Windows-App-Grundlage

## Modulstatus

Jedes Modul hat einen Status:

| Status | Bedeutung |
|--------|-----------|
| produktiv | Modul läuft, ist getestet und freigegeben |
| testbar | Modul läuft, Tests ausstehend |
| entwicklung | Modul in Entwicklung |
| revision | Modul muss überarbeitet werden |
| gesperrt | Modul darf nicht verwendet werden |
| ersetzt | Modul wurde durch neues ersetzt |

## Abhängigkeiten

Module dürfen nur auf Module mit Status `produktiv` oder `testbar` aufbauen. Abhängigkeiten werden im Modulregister dokumentiert.

## Schnittstellen

Jedes Modul definiert:
- Eingabe-Schema
- Ausgabe-Schema
- Fehler-Schema
- Status-Schema

Siehe [`03_Schnittstellen/`](../03_Schnittstellen/).
