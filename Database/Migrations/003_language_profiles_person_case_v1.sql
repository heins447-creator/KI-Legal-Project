-- Sprachkontext Personen, Fall, Kommunikation V1
-- Zweck:
-- 1. Alle 24 EU-Amtssprachen als verfügbarer Katalog.
-- 2. Personalbezogene Einstellung: Anwalt und Sekretariat.
-- 3. Fallbezogene Einstellung: Staat, Landessprache, Prozeßsprache, interne Arbeitssprache.
-- 4. Beteiligtenbezogene Einstellung: Mandant, Gericht, Gegenseite, gegnerischer Anwalt.
-- 5. Kommunikationsbezogene Einstellung: tatsächliche Schreibsprache je Empfängerrolle.

CREATE TABLE IF NOT EXISTS app_languages (
    language_code VARCHAR PRIMARY KEY,
    german_name VARCHAR NOT NULL,
    language_name_de VARCHAR,
    language_name_native VARCHAR,
    language_name_en VARCHAR,
    eu_official BOOLEAN,
    active_in_system BOOLEAN,
    default_enabled BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff_language_profiles (
    staff_key VARCHAR PRIMARY KEY,
    role_key VARCHAR,
    display_name VARCHAR,
    internal_work_language_code VARCHAR,
    accepted_matter_languages_json VARCHAR,
    communication_languages_json VARCHAR,
    document_review_languages_json VARCHAR,
    default_translation_target_language_code VARCHAR,
    active BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_language_profiles (
    case_key VARCHAR PRIMARY KEY,
    case_label VARCHAR,
    jurisdiction_country_code VARCHAR,
    country_language_code VARCHAR,
    procedural_language_code VARCHAR,
    internal_work_language_code VARCHAR,
    source_document_language_code VARCHAR,
    target_document_language_code VARCHAR,
    client_default_language_code VARCHAR,
    opponent_lawyer_default_language_code VARCHAR,
    opponent_party_default_language_code VARCHAR,
    court_default_language_code VARCHAR,
    translation_required BOOLEAN,
    interpreter_required BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_participant_language_profiles (
    participant_profile_key VARCHAR PRIMARY KEY,
    case_key VARCHAR,
    participant_role VARCHAR,
    participant_label VARCHAR,
    mandate_accepted BOOLEAN,
    actual_language_code VARCHAR,
    communication_language_code VARCHAR,
    document_language_code VARCHAR,
    procedural_language_code VARCHAR,
    outgoing_language_code VARCHAR,
    incoming_translation_target_language_code VARCHAR,
    outgoing_translation_source_language_code VARCHAR,
    translation_required BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS communication_language_rules (
    rule_key VARCHAR PRIMARY KEY,
    case_key VARCHAR,
    participant_role VARCHAR,
    default_language_code VARCHAR,
    fallback_language_code VARCHAR,
    procedural_language_code VARCHAR,
    document_language_code VARCHAR,
    translation_required BOOLEAN,
    notes VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS language_profile_audit (
    audit_id VARCHAR PRIMARY KEY,
    audit_time TIMESTAMP,
    audit_area VARCHAR,
    audit_status VARCHAR,
    details VARCHAR
);
