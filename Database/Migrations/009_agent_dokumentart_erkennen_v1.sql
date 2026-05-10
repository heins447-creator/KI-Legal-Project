-- Agent Dokumentart erkennen V1
-- Erster konkreter Agent nach Anwaltvorlage.
-- Der Agent erkennt nur die formale Dokumentart als Vorschlag.
-- Keine Beweiswürdigung, keine Entlastungsbewertung, keine rechtliche Endbewertung.

CREATE TABLE IF NOT EXISTS agent_document_type_suggestion (
    suggestion_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    agent_job_id VARCHAR,
    review_id VARCHAR,
    intake_id VARCHAR,
    case_template_key VARCHAR,
    source_path VARCHAR,
    original_name VARCHAR,
    extension VARCHAR,
    file_exists BOOLEAN,
    size_bytes BIGINT,
    suggested_document_type VARCHAR,
    document_type_group VARCHAR,
    confidence VARCHAR,
    reasons_json VARCHAR,
    extracted_text_hint VARCHAR,
    allowed_next_agent_tasks_json VARCHAR,
    forbidden_conclusions_json VARCHAR,
    status VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_document_type_audit (
    audit_id VARCHAR,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    agent_job_id VARCHAR,
    intake_id VARCHAR,
    details VARCHAR
);
