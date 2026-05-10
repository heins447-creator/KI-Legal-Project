-- Sprachkontext V2 Neuanfang
-- Zweck:
-- Saubere Trennung zwischen Systemsprachen, Personenprofil, Fallprofil,
-- Beteiligtenprofil, Kommunikationssprache, Dokumentensprache und tatsächlicher Sprache.

DROP TABLE IF EXISTS lang_language_catalog;
DROP TABLE IF EXISTS lang_staff_language_settings;
DROP TABLE IF EXISTS lang_case_language_settings;
DROP TABLE IF EXISTS lang_participant_language_settings;
DROP TABLE IF EXISTS lang_intake_language_rules;
DROP TABLE IF EXISTS lang_language_context_audit;

CREATE TABLE lang_language_catalog (
    language_code VARCHAR PRIMARY KEY,
    language_name_de VARCHAR NOT NULL,
    language_name_native VARCHAR,
    iso_639_1 VARCHAR,
    eu_official BOOLEAN,
    available_in_system BOOLEAN,
    selectable_for_staff BOOLEAN,
    selectable_for_case BOOLEAN,
    default_enabled BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE lang_staff_language_settings (
    staff_profile_key VARCHAR PRIMARY KEY,
    role_key VARCHAR,
    display_name VARCHAR,
    internal_work_language_code VARCHAR,
    accepted_matter_languages_json VARCHAR,
    communication_languages_json VARCHAR,
    document_review_languages_json VARCHAR,
    default_draft_language_code VARCHAR,
    default_translation_target_language_code VARCHAR,
    can_accept_foreign_mandates BOOLEAN,
    active BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE lang_case_language_settings (
    case_template_key VARCHAR PRIMARY KEY,
    case_label VARCHAR,
    jurisdiction_country_code VARCHAR,
    legal_area_key VARCHAR,
    country_language_code VARCHAR,
    procedural_language_code VARCHAR,
    internal_work_language_code VARCHAR,
    default_document_language_code VARCHAR,
    default_actual_language_code VARCHAR,
    translation_required_default BOOLEAN,
    interpreter_required_default BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE lang_participant_language_settings (
    participant_profile_key VARCHAR PRIMARY KEY,
    case_template_key VARCHAR,
    participant_role VARCHAR,
    participant_label VARCHAR,
    official_or_procedural_language_code VARCHAR,
    communication_language_code VARCHAR,
    document_language_code VARCHAR,
    actual_or_spoken_language_code VARCHAR,
    fallback_language_code VARCHAR,
    translation_required BOOLEAN,
    created_after_mandate_acceptance BOOLEAN,
    accepted_client_required BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE lang_intake_language_rules (
    intake_rule_key VARCHAR PRIMARY KEY,
    case_template_key VARCHAR,
    incoming_area VARCHAR,
    expected_document_language_code VARCHAR,
    detected_language_policy VARCHAR,
    target_internal_language_code VARCHAR,
    procedural_language_code VARCHAR,
    action_on_mismatch VARCHAR,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE lang_language_context_audit (
    audit_id VARCHAR PRIMARY KEY,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    details VARCHAR
);
