-- Anwaltvorlage Grundmodul V1
-- Der Posteingang ist abgeschlossen. Dieses Modul legt nur die formale Anwaltvorlage an.
-- Keine Beweiswürdigung, keine Entlastungsbewertung, keine endgültige Aktenzuordnung.

CREATE TABLE IF NOT EXISTS anwalt_review_queue (
    review_id VARCHAR,
    intake_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    case_template_key VARCHAR,
    source_path VARCHAR,
    original_name VARCHAR,
    document_language_code VARCHAR,
    detected_languages_json VARCHAR,
    rough_translation_target_language_code VARCHAR,
    rough_translation_available BOOLEAN,
    rough_translation_path VARCHAR,
    safety_status VARCHAR,
    post_intake_status VARCHAR,
    lawyer_review_status VARCHAR,
    minimum_check_json VARCHAR,
    next_required_action VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS anwalt_review_audit (
    audit_id VARCHAR,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    intake_id VARCHAR,
    details VARCHAR
);

CREATE TABLE IF NOT EXISTS anwalt_case_context_template (
    template_key VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    jurisdiction_country_code VARCHAR,
    official_language_code VARCHAR,
    procedural_language_code VARCHAR,
    internal_work_language_code VARCHAR,
    rough_translation_target_language_code VARCHAR,
    matter_type VARCHAR,
    parties_context VARCHAR,
    notes VARCHAR
);
