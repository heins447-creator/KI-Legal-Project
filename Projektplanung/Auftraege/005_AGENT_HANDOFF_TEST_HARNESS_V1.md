# Auftrag 005: AGENT_HANDOFF_TEST_HARNESS_V1

## Ziel

Erzeuge ein Testgerüst für Agentenkommunikation und Übergabeprotokolle.

Dieser Baustein prüft nur Struktur und Beispielübergaben mit künstlichen Testdaten. Keine echten Mandantendaten.

## Grundlage

Pflichtkontext lesen:

- AGENTS.md
- Projektplanung\MASTERPROMPT_KI_LEGAL_PROJECT_V1.md
- Projektplanung\CODING_AGENT_CONTEXT_V1.md
- Projektplanung\MASTER_INDEX.md
- Projektplanung\Agenten\AGENTEN_KONTEXT_SKILL_REGISTER_V1.md
- Config\coding_agent_context_v1.json

## Harte Grenzen

Keine echten Mandantendaten.

Keine rechtliche Endbewertung.

Keine freie Bearbeitung fremder Rechtsgebiete.

Keine Türschwellenmaske.

Keine endgültige Übersetzung.

## Zu erzeugende Pflichtdateien

1. Database\Migrations\015_agent_handoff_test_harness_v1.sql
2. Scripts\python_runner\055_agent_handoff_test_harness_v1.py
3. Scripts\python_runner\056_check_agent_handoff_test_harness_v1.py
4. Scripts\Run_Agent_Handoff_Test_Harness.ps1
5. Projektplanung\Agenten\AGENT_HANDOFF_TEST_HARNESS_V1.md

## Datenbankinhalt

Lege Tabellen oder Erweiterungen an für:

- agent_handoff_test_case
- agent_handoff_test_message
- agent_handoff_test_result
- agent_handoff_validation_rule

## Startdaten

Künstliche Testfälle ohne echte Mandantendaten:

1. Arbeitsrecht Schweden fragt Medizinrecht an.
2. Arbeitsrecht Schweden fragt Sozialrecht an.
3. Arbeitsrecht Schweden fragt Zivilrecht an.

Jede Übergabe enthält:

- Ausgangsfrage
- betroffene Rechtsgebiete
- Land und Rechtssystem
- Dokumentfundstelle als künstlicher Platzhalter
- Unsicherheitsgrad
- konkrete Prüfbitte
- Antwort mit künstlicher Quelle/Fundstelle
- Rückgabe an federführenden Agenten

## Prüfpflicht

Prüfe, daß kein Agent fremdes Rechtsgebiet selbst übernimmt.

Prüfe, daß jede Übergabe Fundstelle, Unsicherheit und Zielagent enthält.

Prüfe, daß künstliche Testdaten klar gekennzeichnet sind.

.NET-Build darf nicht brechen.

Am Ende Git-Status sauber vorbereiten.