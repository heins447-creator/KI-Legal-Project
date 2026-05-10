-- Agent Sachverhaltsbezug V1
-- Dritte konkrete Agentenfunktion.
-- Der Agent bereitet nur einen moeglichen Sachverhaltsbezug vor.
-- Keine Beweiswuerdigung, keine Entlastungsbewertung, keine rechtliche Endbewertung.

CREATE TABLE IF NOT EXISTS agent_fact_context_suggestion (
    fact_context_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    agent_job_id VARCHAR,
    review_id VARCHAR,
    intake_id VARCHAR,
    case_template_key VARCHAR,
    source_path VARCHAR,
    original_name VARCHAR,
    source_document_type VARCHAR,
    source_document_language_code VARCHAR,
    suggested_context_key VARCHAR,
    suggested_context_label VARCHAR,
    confidence VARCHAR,
    timeline_hint_date VARCHAR,
    participant_hints_json VARCHAR,
    reason_terms_json VARCHAR,
    text_extract VARCHAR,
    allowed_next_agent_tasks_json VARCHAR,
    forbidden_conclusions_json VARCHAR,
    status VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_fact_context_audit (
    audit_id VARCHAR,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    agent_job_id VARCHAR,
    intake_id VARCHAR,
    details VARCHAR
);
