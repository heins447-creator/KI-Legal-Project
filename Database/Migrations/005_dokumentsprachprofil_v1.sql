-- Dokumentsprachprofil V1
-- Dokumentiert die Spracherkennung je Eingang/Dokument.
-- Es erfolgt keine Beweiswürdigung und keine endgültige Aktenzuordnung.

CREATE TABLE IF NOT EXISTS posteingang_document_language_profile (
    document_language_id VARCHAR PRIMARY KEY,
    intake_id VARCHAR,
    document_key VARCHAR,
    mandant_key VARCHAR,
    case_key VARCHAR,
    source_area VARCHAR,
    source_path VARCHAR,
    original_name VARCHAR,
    detected_primary_language_code VARCHAR,
    detected_language_codes_json VARCHAR,
    detected_secondary_language_codes_json VARCHAR,
    is_multilingual BOOLEAN,
    internal_work_language_code VARCHAR,
    rough_translation_target_language_code VARCHAR,
    rough_translation_required BOOLEAN,
    procedural_language_code VARCHAR,
    official_language_code VARCHAR,
    language_routing_key VARCHAR,
    confidence VARCHAR,
    detection_basis VARCHAR,
    status VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posteingang_document_language_audit (
    audit_id VARCHAR PRIMARY KEY,
    audit_time TIMESTAMP,
    document_language_id VARCHAR,
    intake_id VARCHAR,
    audit_status VARCHAR,
    details VARCHAR
);
