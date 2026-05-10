# Agent Sprache und Übersetzung V1

## Zweck

Dies ist die zweite konkrete Agentenfunktion nach dem Agenten `DOKUMENTART_ERKENNEN`.

Der Agent prüft:

- Dokumentsprache
- tatsächlich erkannte Sprache
- Mehrsprachigkeit
- Zielarbeitssprache Deutsch
- grobe Arbeitsübersetzung nach Deutsch

## Grenze

Der Agent erstellt keine beglaubigte Übersetzung.

Der Agent bewertet nicht:

- Beweiswert
- Entlastungswert
- rechtliche Relevanz
- prozessuale Verwertbarkeit
- endgültige Aktenzuordnung

## Fallkontext Schweden Arbeitsrecht

- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- Arbeitsübersetzung für den Anwalt: Deutsch

## Arbeitsweise V1

V1 nutzt:

- vorhandenes Dokumentsprachprofil
- vorhandene Anwaltvorlage
- vorhandene Agentenaufgabe
- Dateiname
- einfache Textauszüge bei direkt lesbaren Textdateien

Bei PDF, DOCX, Bild oder Scan wird die Übersetzung als technisch vorbereitet markiert. Die eigentliche OCR-, Parser-, Google- oder KI-Übersetzung kann danach angebunden werden.

## Datenbanktabellen

Angelegt werden:

- `agent_language_translation_review`
- `agent_language_translation_audit`

Die vorhandene Tabelle `agent_work_queue` wird aktualisiert.

## Übersetzungsordner

Grobe Arbeitsübersetzungen und Übersetzungshinweise werden abgelegt unter:

`I:\KI_Legal_Project\Posteingang\96_Uebersetzung_DE`

## Starter

Direktstart:

`I:\KI_Legal_Project\Scripts\Run_Agent_Sprache_Uebersetzung.ps1`
