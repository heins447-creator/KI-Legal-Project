# Agent Dokumentart erkennen V1

## Zweck

Dies ist die erste konkrete Agentenfunktion nach Posteingang, Anwaltvorlage und Agenten-Grundmodul.

Der Agent erkennt nur die formale Dokumentart.

## Zulässige Aufgabe

Der Agent darf vorschlagen, ob es sich formal etwa handelt um:

- Schriftsatz
- Korrespondenz
- Nachweis
- Aussage
- Verwaltungsdokument
- Protokoll
- Bild
- technische Liste
- unklare Dokumentart

## Grenze

Der Agent entscheidet nicht:

- Beweiswert
- Entlastungswert
- rechtliche Relevanz
- prozessuale Verwertbarkeit
- endgültige Aktenzuordnung
- Klageentscheidung

## Arbeitsweise

Der Agent wertet aus:

- Dateiname
- Dateiendung
- vorhandene Quelle aus der Anwaltvorlage
- kleiner Textauszug bei einfachen Textdateien

PDF, DOCX und Bilddateien werden in V1 nur anhand äußerer Merkmale und Dateinamen bewertet. Tieferes Auslesen folgt erst in späteren Agenten.

## Datenbanktabellen

Angelegt werden:

- `agent_document_type_suggestion`
- `agent_document_type_audit`

Die vorhandene Tabelle `agent_work_queue` wird aktualisiert.

## Starter

Direktstart:

`I:\KI_Legal_Project\Scripts\Run_Agent_Dokumentart.ps1`
