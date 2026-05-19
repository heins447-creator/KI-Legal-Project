# SOURCE_ADAPTER_HEALTHCHECK_FRAMEWORK_V1

## Zweck

Grundgeruest fuer Quellenadapter und Healthcheck-Logik. Dieser Baustein fuehrt **keinen** echten Liveabruf aus. Er legt nur Struktur, Konfiguration, Dry-Run-Pruefung und spaetere Sicherheitslogik an.

## Bestandteile

| Nr. | Datei | Zweck |
|-----|-------|-------|
| 1 | `Database\Migrations\014_source_adapter_healthcheck_framework_v1.sql` | Tabellen fuer Adapter, Endpoints, Dry-Run-Checks, Sicherheitsregeln, Offline-Fallbacks, Run-Log |
| 2 | `Scripts\python_runner\053_source_adapter_healthcheck_framework_v1.py` | Laeufer: Migration, Startdaten, Dry-Run-Checks |
| 3 | `Scripts\python_runner\054_check_source_adapter_healthcheck_framework_v1.py` | Pruefdatei: Tabellen, Regeln, Dry-Run-Only-Nachweis |
| 4 | `Scripts\Run_Source_Adapter_Healthcheck_Framework.ps1` | PowerShell-Starter |
| 5 | `Config\source_adapter_policy_v1.json` | Richtlinienkonfiguration |
| 6 | `Projektplanung\Quellen\SOURCE_ADAPTER_HEALTHCHECK_FRAMEWORK_V1.md` | Diese Dokumentation |

## Datenbanktabellen

### source_adapter_policy
Richtlinien fuer jeden Adaptertyp:
- `policy_code` – Primaerschluessel
- `adapter_type` – REST, HTML-Metadaten, Download-Manuell, Offline-Cache
- `allowed_scope` – Standard: `dryrun_only`
- `live_run_enabled` – Standard: `FALSE`
- `auth_required` – Ob Authentifizierung erforderlich ist
- `credential_storage_rule` – `keine_im_klartext`
- `allowed_domain_pattern` – Nur freigegebene Domains (z.B. `*.europa.eu`)
- `offline_fallback_enabled` – Ob Offline-Fallback verfuegbar ist

### source_adapter_endpoint
Endpoints als Dry-Run-Platzhalter:
- `endpoint_code` – Primaerschluessel
- `policy_code` – Fremdschluessel zu Policy
- `endpoint_url_hint` – URL-Hinweis ohne aktiven Abruf
- `endpoint_type` – `dryrun_placeholder`
- `active` – Standard: `FALSE`

### source_adapter_dryrun_check
Simulierte Pruefungen ohne Netzwerk:
- `check_code` – Primaerschluessel
- `endpoint_code` – Fremdschluessel
- `check_type` – `schema_validierung`, `auth_konfiguration_pruefung`, `offline_fallback_verfuegbarkeit`, ...
- `check_result` – `bestanden`, `nicht_geprueft`
- `passed` – Boolean

### source_adapter_security_rule
Sicherheitsregeln:
- `rule_code` – Primaerschluessel
- `rule_type` – `domain_whitelist`, `no_credentials_in_code`, `dryrun_only_default`
- `rule_expression` – SQL-aehnlicher Ausdruck zur Pruefung
- `rule_action` – `blockieren`, `erlauben_nach_freigabe`
- `active` – Boolean

### source_adapter_offline_fallback
Offline-Fallback-Strategien:
- `fallback_code` – Primaerschluessel
- `fallback_type` – `metadaten_cache`, `html_snapshot`, `thesaurus_dump`
- `fallback_available` – Boolean

### source_adapter_run_log
Laufprotokoll:
- `log_id` – Primaerschluessel
- `run_type` – `dryrun` oder `live`
- `network_used` – Boolean (Standard: `FALSE`)

## Harte Grenzen

- **Kein echter Internetabruf** im Standardlauf.
- **Keine freie Internetrecherche.**
- **Nur vorbereitete und freigegebene Quellen** duerfen spaeter adressiert werden.
- **Keine Massendaten.**
- **Keine API-Schluessel.**
- **Keine echten Mandantendaten.**
- **Keine Credentials im Klartext.**

## Adaptertypen

| Typ | Live erlaubt | Auth erforderlich | Credential-Regel |
|-----|-------------|-------------------|------------------|
| REST | Nein | Ja | `keine_im_klartext` |
| HTML-Metadaten | Nein | Nein | `keine_im_klartext` |
| Download-Manuell | Nein | Nein | `nicht_anwendbar` |
| Offline-Cache | Nein | Nein | `nicht_anwendbar` |

## Freigabe-Hierarchie

Falls spaeter Live-Runs ermoeglicht werden:
1. Agent
2. Quellenbetreuer
3. Anwalt
4. Admin

## Naechster Schritt

Integration mit dem Quellenkandidaten-Register (003) und spaeterer Live-Freigabe durch den Quellenbetreuer.
