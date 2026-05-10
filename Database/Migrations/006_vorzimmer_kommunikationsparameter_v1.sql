-- Vorzimmer Kommunikationsparameter V1
-- Zweck:
-- Das Vorzimmer kann Grundparameter für Kommunikation, Sprache, Land, Gericht und Beteiligte pflegen.
-- Der Posteingang bewertet keine Beweise und keine rechtliche Erheblichkeit.

CREATE TABLE IF NOT EXISTS vz_language_package_catalog (
    language_code VARCHAR PRIMARY KEY,
    language_name_de VARCHAR,
    eu_official BOOLEAN,
    available BOOLEAN,
    default_target_for_work_translation BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vz_communication_context_template (
    template_key VARCHAR PRIMARY KEY,
    case_type VARCHAR,
    jurisdiction_country_code VARCHAR,
    official_language_code VARCHAR,
    procedural_language_code VARCHAR,
    internal_work_language_code VARCHAR,
    rough_translation_target_language_code VARCHAR,
    default_document_language_code VARCHAR,
    notes VARCHAR,
    editable BOOLEAN,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vz_participant_communication_profile (
    profile_key VARCHAR PRIMARY KEY,
    template_key VARCHAR,
    participant_role VARCHAR,
    participant_label VARCHAR,
    country_code VARCHAR,
    expected_language_code VARCHAR,
    communication_language_code VARCHAR,
    document_language_code VARCHAR,
    rough_translation_target_language_code VARCHAR,
    created_after_mandate_acceptance BOOLEAN,
    accepted_client_required BOOLEAN,
    editable BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vz_address_language_inference_rule (
    rule_key VARCHAR PRIMARY KEY,
    country_code VARCHAR,
    postal_code_prefix VARCHAR,
    address_contains VARCHAR,
    language_code VARCHAR,
    confidence_level VARCHAR,
    notes VARCHAR,
    active BOOLEAN,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vz_communication_parameter_audit (
    audit_id VARCHAR PRIMARY KEY,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    details VARCHAR
);
