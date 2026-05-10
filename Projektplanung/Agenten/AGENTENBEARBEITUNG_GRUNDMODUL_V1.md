# Agentenbearbeitung Grundmodul V1

## Zweck

Dieses Modul beginnt die nachgelagerte Bearbeitung nach Posteingang und Anwaltvorlage.

Der Posteingang hat bis hierher nur Sicherheit, Sprache, Übersetzungsbedarf, Kommunikationsparameter und formale Vorlage vorbereitet.

Die Agentenbearbeitung darf jetzt Aktenstruktur, Dokumentart, Sachverhaltsbezug und mögliche Beweis- oder Entlastungsrichtung vorbereiten.

## Grenze

Die Agentenbearbeitung entscheidet nicht abschließend:

- Beweiswert
- Entlastungswert
- Aussagequalität
- rechtliche Relevanz
- endgültige Aktenzuordnung
- Klageentscheidung
- Schriftsatzfreigabe

Alle Ergebnisse sind Vorschläge zur anwaltlichen Prüfung.

## Fallkontext Schweden Arbeitsrecht

- Staat: Schweden
- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- Streit: Arbeitnehmer gegen kommunalen Arbeitgeber

## Tabellen

Angelegt werden:

- `agent_task_catalog`
- `agent_case_scope`
- `agent_work_queue`
- `agent_processing_audit`

## Aufgaben

V1 legt folgende Aufgaben je Anwaltvorlage an:

1. Dokumentart erkennen
2. Sprache und Arbeitsübersetzung prüfen
3. Sachverhaltsbezug vorbereiten
4. Beweis- oder Entlastungsvorschlag vorbereiten
5. Anwaltvorlage strukturieren

## Starter

Direktstart:

`I:\KI_Legal_Project\Scripts\Run_Agentenbearbeitung.ps1`
