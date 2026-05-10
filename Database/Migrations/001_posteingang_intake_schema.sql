-- Posteingang Datenmodell V1
-- Zweck:
-- Der Posteingang ist ein vorgelagerter Sicherheits- und Entscheidungsbereich.
-- Ungeprüfte Dateien werden nicht unmittelbar als normales Dokument übernommen.
-- Gespeichert werden Eingangsvermerk, technische Prüfergebnisse, Absenderstatus,
-- Quarantänestatus und Vorzimmerentscheidung.

CREATE TABLE IF NOT EXISTS posteingang_intake (
    intake_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP DEFAULT current_timestamp,
    updated_at TIMESTAMP,
    source_channel VARCHAR,
    source_reference VARCHAR,
    original_file_name VARCHAR,
    original_extension VARCHAR,
    original_size_bytes BIGINT,
    original_hash_sha256 VARCHAR,
    staged_path VARCHAR,
    quarantine_path VARCHAR,
    sender_claimed_name VARCHAR,
    sender_claimed_address VARCHAR,
    sender_verified_status VARCHAR DEFAULT 'ungeprueft',
    signature_status VARCHAR DEFAULT 'nicht_geprueft',
    certificate_subject VARCHAR,
    certificate_issuer VARCHAR,
    certificate_thumbprint VARCHAR,
    malware_scan_status VARCHAR DEFAULT 'nicht_geprueft',
    archive_unpack_status VARCHAR DEFAULT 'nicht_erforderlich',
    file_type_claimed VARCHAR,
    file_type_detected VARCHAR,
    language_detected VARCHAR,
    short_summary_de VARCHAR,
    document_guess VARCHAR,
    case_candidate_id VARCHAR,
    provisional_matter_ref VARCHAR,
    intake_status VARCHAR DEFAULT 'eingang',
    risk_level VARCHAR DEFAULT 'ungeprueft',
    secretary_decision VARCHAR DEFAULT 'offen',
    lawyer_submission_status VARCHAR DEFAULT 'nicht_vorgelegt',
    decision_note VARCHAR,
    normal_document_id BIGINT,
    released_at TIMESTAMP,
    released_by VARCHAR
);

CREATE TABLE IF NOT EXISTS posteingang_checks (
    check_id VARCHAR PRIMARY KEY,
    intake_id VARCHAR,
    created_at TIMESTAMP DEFAULT current_timestamp,
    check_type VARCHAR,
    check_tool VARCHAR,
    result_status VARCHAR,
    severity VARCHAR,
    details VARCHAR
);

CREATE TABLE IF NOT EXISTS posteingang_decisions (
    decision_id VARCHAR PRIMARY KEY,
    intake_id VARCHAR,
    created_at TIMESTAMP DEFAULT current_timestamp,
    role_name VARCHAR,
    decision_type VARCHAR,
    decision_result VARCHAR,
    note VARCHAR
);

CREATE TABLE IF NOT EXISTS posteingang_events (
    event_id VARCHAR PRIMARY KEY,
    intake_id VARCHAR,
    created_at TIMESTAMP DEFAULT current_timestamp,
    event_type VARCHAR,
    event_text VARCHAR
);

CREATE TABLE IF NOT EXISTS posteingang_allowed_research_sources (
    source_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP DEFAULT current_timestamp,
    source_group VARCHAR,
    source_name VARCHAR,
    source_url VARCHAR,
    jurisdiction VARCHAR,
    trust_level VARCHAR,
    note VARCHAR
);

INSERT INTO posteingang_allowed_research_sources
    (source_id, source_group, source_name, source_url, jurisdiction, trust_level, note)
SELECT
    'SRC-GOV-001',
    'staatliche_quelle',
    'Staatliche und gerichtliche Quellen',
    '',
    'mehrere',
    'hoch',
    'Platzhalter für spätere gepflegte Quellenliste'
WHERE NOT EXISTS (
    SELECT 1 FROM posteingang_allowed_research_sources WHERE source_id = 'SRC-GOV-001'
);

INSERT INTO posteingang_allowed_research_sources
    (source_id, source_group, source_name, source_url, jurisdiction, trust_level, note)
SELECT
    'SRC-LAW-001',
    'juristische_fachquelle',
    'Juristische Fachquellen, Universitäten, Urteilsdatenbanken und Fachverlage',
    '',
    'mehrere',
    'hoch',
    'Platzhalter für spätere gepflegte Quellenliste'
WHERE NOT EXISTS (
    SELECT 1 FROM posteingang_allowed_research_sources WHERE source_id = 'SRC-LAW-001'
);
