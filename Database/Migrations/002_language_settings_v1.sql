-- SPRACHGRUNDLAGEN V1
-- Zweck: Grundeinstellungen für 24 EU-Amtssprachen, Rollenarbeitssprache und Fallsprachprofil.
-- Anwendung: I:\KI_Legal_Project\Database\Legal_Brain.duckdb

CREATE TABLE IF NOT EXISTS app_languages (
    language_code VARCHAR PRIMARY KEY,
    german_name VARCHAR NOT NULL,
    native_name VARCHAR,
    english_name VARCHAR,
    eu_official BOOLEAN NOT NULL DEFAULT true,
    active_in_system BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS software_language_settings (
    setting_key VARCHAR PRIMARY KEY,
    default_ui_language_code VARCHAR NOT NULL,
    default_internal_work_language_code VARCHAR NOT NULL,
    fallback_translation_language_code VARCHAR NOT NULL,
    require_case_language_profile BOOLEAN NOT NULL DEFAULT true,
    notes VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_language_settings (
    role_key VARCHAR PRIMARY KEY,
    role_display_name VARCHAR NOT NULL,
    ui_language_code VARCHAR NOT NULL,
    internal_work_language_code VARCHAR NOT NULL,
    notes VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_mandate_languages (
    role_key VARCHAR NOT NULL,
    language_code VARCHAR NOT NULL,
    accepts_mandates BOOLEAN NOT NULL DEFAULT false,
    accepts_communication BOOLEAN NOT NULL DEFAULT false,
    notes VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(role_key, language_code)
);

CREATE TABLE IF NOT EXISTS case_language_profiles (
    case_key VARCHAR PRIMARY KEY,
    case_name VARCHAR NOT NULL,
    jurisdiction_country_code VARCHAR NOT NULL,
    jurisdiction_name VARCHAR NOT NULL,
    law_area VARCHAR NOT NULL,
    national_language_code VARCHAR NOT NULL,
    procedural_language_code VARCHAR NOT NULL,
    internal_work_language_code VARCHAR NOT NULL,
    client_communication_language_code VARCHAR,
    opponent_communication_language_code VARCHAR,
    opponent_lawyer_language_code VARCHAR,
    translation_required BOOLEAN NOT NULL DEFAULT true,
    notes VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posteingang_language_profiles (
    intake_id VARCHAR PRIMARY KEY,
    original_name VARCHAR,
    declared_language_code VARCHAR,
    detected_language_code VARCHAR,
    jurisdiction_country_code VARCHAR,
    procedural_language_code VARCHAR,
    internal_work_language_code VARCHAR,
    translation_required BOOLEAN,
    confidence VARCHAR,
    notes VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
