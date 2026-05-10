# Agent Sachverhaltsbezug V1

## Zweck

Dies ist die dritte konkrete Agentenfunktion nach:

1. Dokumentart erkennen
2. Sprache und Übersetzung prüfen

Der Agent bereitet nur einen möglichen Sachverhaltsbezug vor.

## Fallkontext

Es handelt sich um einen schwedischen Arbeitsrechtsstreit zwischen Arbeitnehmer und kommunalem Arbeitgeber.

- Amtssprache: Schwedisch
- Prozeßsprache: Schwedisch
- interne Arbeitssprache: Deutsch
- Arbeitsübersetzung für den Anwalt: Deutsch

## Zulässige Aufgabe

Der Agent darf einen vorläufigen Sachverhaltsbereich vorschlagen, etwa:

- Anstellung, Vertrag oder Beschäftigungsgrundlage
- Unterricht, Schulorganisation oder pädagogischer Ablauf
- Warnung, Maßnahme oder dienstliche Reaktion
- Kündigung, Ausschluß, Hausverbot oder Beendigung
- Arbeitsumfeld, Arbeitsmiljö oder organisatorische Belastung
- Eltern-, Schüler- oder Außenkommunikation
- Behörde, Gericht oder Verfahren
- zeitlicher Ablauf oder Chronologie
- sonstiger oder unklarer Sachverhaltsbezug

## Grenze

Der Agent entscheidet nicht:

- Beweiswert
- Entlastungswert
- rechtliche Relevanz
- prozessuale Verwertbarkeit
- Verschulden
- Glaubwürdigkeit
- endgültige Aktenzuordnung
- Klageentscheidung

## Arbeitsweise V1

V1 nutzt:

- vorhandene Agentenaufgaben
- vorhandene Dokumentartvorschläge
- vorhandene Sprach- und Übersetzungsprüfung
- Dateiname
- einfache Textauszüge bei direkt lesbaren Textdateien

PDF, DOCX, Bild und Scan werden in V1 vor allem anhand von Dateiname, vorheriger Dokumentart und vorhandenen Metadaten eingeordnet.

## Datenbanktabellen

Angelegt werden:

- `agent_fact_context_suggestion`
- `agent_fact_context_audit`

Die vorhandene Tabelle `agent_work_queue` wird aktualisiert.

## Starter

Direktstart:

`I:\KI_Legal_Project\Scripts\Run_Agent_Sachverhaltsbezug.ps1`
