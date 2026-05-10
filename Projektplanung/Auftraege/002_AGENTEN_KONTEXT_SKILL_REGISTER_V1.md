# Auftrag 002: AGENTEN_KONTEXT_SKILL_REGISTER_V1

## Ziel

Erzeuge das Grundgerüst für ein Agenten-Kontext- und Skill-Register.

Dieser Baustein kommt nach dem Quellenbetreuer und vor der Türschwelle.

## Grundlage

Pflichtkontext lesen:

- AGENTS.md
- Projektplanung\MASTERPROMPT_KI_LEGAL_PROJECT_V1.md
- Projektplanung\CODING_AGENT_CONTEXT_V1.md
- Projektplanung\MASTER_INDEX.md
- Projektplanung\Quellen\QUELLENBETREUER_FACHANWALTSRASTER_V1.md
- Config\coding_agent_context_v1.json

## Harte Grenzen

Keine echten Mandantendaten.

Keine freie Internetrecherche.

Keine API-Schlüssel.

Keine Türschwellenmaske programmieren.

Keine endgültige Übersetzung programmieren.

Keine rechtliche Endbewertung.

Keine Agentenentscheidung außerhalb des jeweils zuständigen Rechtsgebiets.

## Fachlicher Ausgangspunkt

Erster Testfall:

- Land: Schweden
- Rechtsgebiet: Arbeitsrecht
- Ausgangssprache: Schwedisch
- Kanzleisprache: Deutsch
- Sprachpaket: sv_de_arbeitsrecht_se
- erste Dokumente: Arbeitsvertrag und Kündigung

## Zu erzeugende Pflichtdateien

1. Database\Migrations\012_agenten_kontext_skill_register_v1.sql
2. Scripts\python_runner\048_agenten_kontext_skill_register_v1.py
3. Scripts\python_runner\049_check_agenten_kontext_skill_register_v1.py
4. Scripts\Run_Agenten_Kontext_Skill_Register.ps1
5. Projektplanung\Agenten\AGENTEN_KONTEXT_SKILL_REGISTER_V1.md

## Datenbankinhalt

Lege Tabellen an für:

- agent_role_registry
- agent_skill_registry
- agent_scope_rule
- agent_handoff_protocol
- agent_handoff_route
- agent_uncertainty_rule
- agent_source_binding
- agent_language_package_binding

## Startdaten

Mindestens vorbereiten:

- federführender Arbeitsrechtsagent Schweden
- Quellenbetreuer-Agent
- Sprachpaket-Agent sv_de_arbeitsrecht_se
- Medizinrecht-Prüfagent als fremdes Rechtsgebiet nur für spätere Übergabe
- Sozialrecht-Prüfagent als fremdes Rechtsgebiet nur für spätere Übergabe
- Zivilrecht-Prüfagent als fremdes Rechtsgebiet nur für spätere Übergabe

## Übergabelogik

Ein Agent darf fremde Rechtsgebiete nicht selbst bearbeiten.

Bei fachübergreifender Frage muß er eine strukturierte Prüfbitte erzeugen:

- Ausgangsfrage
- betroffene Rechtsgebiete
- Land und Rechtssystem
- Dokumentfundstelle
- Unsicherheitsgrad
- konkrete Prüfbitte
- Antwort mit Quelle und Fundstelle
- Rückgabe an federführenden Agenten

## Technische Pflicht

Alle Dateien müssen syntaktisch gültig sein.

Python-Prüfdatei muß die Tabellen und Startdaten prüfen.

PowerShell-Starter muß Läufer und Prüfung ausführen.

Keine Massendaten.

Keine echte Internetverbindung.

Berichte nach Windows_App\Logs.

Am Ende Git-Status sauber vorbereiten.
