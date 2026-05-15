-- Migration 014: Source Adapter Healthcheck Framework V1
-- Ziel: Grundgeruest fuer Quellenadapter, Healthcheck-Logik, Dry-Run und Sicherheitsregeln.
-- Harte Grenze: Kein echter Internetabruf im Standardlauf.

CREATE TABLE IF NOT EXISTS source_adapter_policy (
    policy_code VARCHAR PRIMARY KEY,
    policy_name VARCHAR NOT NULL,
    adapter_type VARCHAR NOT NULL,
    allowed_scope VARCHAR DEFAULT 'dryrun_only',
    live_run_enabled BOOLEAN DEFAULT FALSE,
    auth_required BOOLEAN DEFAULT FALSE,
    credential_storage_rule VARCHAR DEFAULT 'keine_im_klartext',
    allowed_domain_pattern VARCHAR,
    offline_fallback_enabled BOOLEAN DEFAULT FALSE,
    notes_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_adapter_endpoint (
    endpoint_code VARCHAR PRIMARY KEY,
    policy_code VARCHAR NOT NULL,
    endpoint_url_hint VARCHAR,
    endpoint_type VARCHAR DEFAULT 'dryrun_placeholder',
    active BOOLEAN DEFAULT FALSE,
    last_dryrun_at TIMESTAMP,
    last_live_run_at TIMESTAMP,
    dryrun_result VARCHAR,
    notes_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_adapter_dryrun_check (
    check_code VARCHAR PRIMARY KEY,
    endpoint_code VARCHAR NOT NULL,
    check_type VARCHAR NOT NULL,
    check_result VARCHAR DEFAULT 'nicht_geprueft',
    check_detail_de VARCHAR,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    passed BOOLEAN,
    notes_de VARCHAR
);

CREATE TABLE IF NOT EXISTS source_adapter_security_rule (
    rule_code VARCHAR PRIMARY KEY,
    policy_code VARCHAR NOT NULL,
    rule_type VARCHAR NOT NULL,
    rule_expression VARCHAR NOT NULL,
    rule_action VARCHAR DEFAULT 'blockieren',
    active BOOLEAN DEFAULT TRUE,
    rule_note_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_adapter_offline_fallback (
    fallback_code VARCHAR PRIMARY KEY,
    policy_code VARCHAR NOT NULL,
    fallback_type VARCHAR NOT NULL,
    fallback_content_hint VARCHAR,
    fallback_available BOOLEAN DEFAULT FALSE,
    last_verified_at TIMESTAMP,
    notes_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_adapter_run_log (
    log_id VARCHAR PRIMARY KEY,
    policy_code VARCHAR NOT NULL,
    endpoint_code VARCHAR,
    run_type VARCHAR NOT NULL,
    run_status VARCHAR DEFAULT 'gestartet',
    run_result_de VARCHAR,
    http_status INTEGER,
    network_used BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    notes_de VARCHAR
);
