# Auftrag 004: SOURCE_ADAPTER_HEALTHCHECK_FRAMEWORK_V1

## Ziel

Erzeuge ein Grundgerüst für Quellenadapter und Healthcheck-Logik.

Dieser Baustein führt noch keinen echten Liveabruf aus. Er legt nur Struktur, Konfiguration, Dry-Run-Prüfung und spätere Sicherheitslogik an.

## Grundlage

Pflichtkontext lesen:

- AGENTS.md
- Projektplanung\MASTERPROMPT_KI_LEGAL_PROJECT_V1.md
- Projektplanung\CODING_AGENT_CONTEXT_V1.md
- Projektplanung\MASTER_INDEX.md
- Projektplanung\Quellen\QUELLENBETREUER_FACHANWALTSRASTER_V1.md
- Projektplanung\Quellen\QUELLENKANDIDATEN_EU_SE_OFFICIAL_SOURCES_V1.md
- Config\coding_agent_context_v1.json

## Harte Grenzen

Kein echter Internetabruf im Standardlauf.

Keine freie Internetrecherche.

Nur vorbereitete und freigegebene Quellen dürfen später adressiert werden.

Keine Massendaten.

Keine API-Schlüssel.

Keine echten Mandantendaten.

## Zu erzeugende Pflichtdateien

1. Database\Migrations\014_source_adapter_healthcheck_framework_v1.sql
2. Scripts\python_runner\053_source_adapter_healthcheck_framework_v1.py
3. Scripts\python_runner\054_check_source_adapter_healthcheck_framework_v1.py
4. Scripts\Run_Source_Adapter_Healthcheck_Framework.ps1
5. Projektplanung\Quellen\SOURCE_ADAPTER_HEALTHCHECK_FRAMEWORK_V1.md
6. Config\source_adapter_policy_v1.json

## Datenbankinhalt

Lege Tabellen oder Erweiterungen an für:

- source_adapter_policy
- source_adapter_endpoint
- source_adapter_dryrun_check
- source_adapter_security_rule
- source_adapter_offline_fallback
- source_adapter_run_log

## Startdaten

Mindestens vorbereiten:

- Adaptertyp REST
- Adaptertyp HTML-Metadaten
- Adaptertyp Download-Manuell
- Adaptertyp Offline-Cache
- Dry-Run ohne Netzverbindung
- Live-Run gesperrt bis Freigabe
- keine Credentials im Klartext
- nur freigegebene Domain/Quelle

## Technische Pflicht

Der Python-Läufer darf im Standardlauf keinen HTTP-Request ausführen.

Die Prüfdatei muß beweisen, daß der Standardlauf nur Dry-Run ist.

PowerShell-Starter muß Läufer und Prüfung ausführen.

.NET-Build darf nicht brechen.

Am Ende Git-Status sauber vorbereiten.