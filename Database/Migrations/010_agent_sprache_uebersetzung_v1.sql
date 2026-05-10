-- Agent Sprache und Uebersetzung V1
-- Zweiter konkreter Agent nach Dokumentart.
-- Der Agent prüft Sprache, Mehrsprachigkeit und deutsche Arbeitsuebersetzung.
-- Keine beglaubigte Uebersetzung, keine rechtliche Bewertung.

CREATE TABLE IF NOT EXISTS agent_language_translation_review (
    translation_review_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    agent_job_id VARCHAR,
    review_id VARCHAR,
    intake_id VARCHAR,
    case_template_key VARCHAR,
    source_path VARCHAR,
    original_name VARCHAR,
    document_language_code VARCHAR,
    detected_language_code VARCHAR,
    additional_languages_json VARCHAR,
    is_multilingual BOOLEAN,
    target_language_code VARCHAR,
    rough_translation_required BOOLEAN,
    rough_translation_possible BOOLEAN,
    rough_translation_status VARCHAR,
    rough_translation_path VARCHAR,
    source_text_extract VARCHAR,
    translation_note VARCHAR,
    confidence VARCHAR,
    forbidden_conclusions_json VARCHAR,
    status VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_language_translation_audit (
    audit_id VARCHAR,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    agent_job_id VARCHAR,
    intake_id VARCHAR,
    details VARCHAR
);
