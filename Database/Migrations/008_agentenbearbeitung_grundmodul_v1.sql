-- Agentenbearbeitung Grundmodul V1
-- Nachgelagerte Bearbeitung nach Posteingang und Anwaltvorlage.
-- Dieses Modul legt nur Aufgaben, Arbeitsliste und Grenzen an.
-- Keine abschließende anwaltliche Entscheidung.

CREATE TABLE IF NOT EXISTS agent_task_catalog (
    task_key VARCHAR,
    task_order INTEGER,
    task_label VARCHAR,
    task_scope VARCHAR,
    allowed_output VARCHAR,
    forbidden_output VARCHAR,
    active BOOLEAN,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_case_scope (
    scope_key VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    case_template_key VARCHAR,
    jurisdiction_country_code VARCHAR,
    official_language_code VARCHAR,
    procedural_language_code VARCHAR,
    internal_work_language_code VARCHAR,
    matter_type VARCHAR,
    parties_context VARCHAR,
    scope_notes VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_work_queue (
    agent_job_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    review_id VARCHAR,
    intake_id VARCHAR,
    case_template_key VARCHAR,
    source_path VARCHAR,
    original_name VARCHAR,
    document_language_code VARCHAR,
    rough_translation_target_language_code VARCHAR,
    task_key VARCHAR,
    task_order INTEGER,
    job_status VARCHAR,
    priority INTEGER,
    allowed_scope VARCHAR,
    forbidden_scope VARCHAR,
    expected_output_json VARCHAR,
    result_json VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_processing_audit (
    audit_id VARCHAR,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    intake_id VARCHAR,
    task_key VARCHAR,
    details VARCHAR
);
