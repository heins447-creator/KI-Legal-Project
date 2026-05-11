CREATE TABLE IF NOT EXISTS agent_role_registry (
    role_code VARCHAR PRIMARY KEY,
    role_name_de VARCHAR NOT NULL,
    role_description_de VARCHAR NOT NULL,
    country_code VARCHAR NOT NULL,
    language_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR NOT NULL,
    source_language_code VARCHAR NOT NULL,
    target_language_code VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_skill_registry (
    skill_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    skill_name_de VARCHAR NOT NULL,
    skill_description_de VARCHAR NOT NULL,
    skill_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_scope_rule (
    rule_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    country_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR NOT NULL,
    allowed_scope_de VARCHAR NOT NULL,
    forbidden_scope_de VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_handoff_protocol (
    protocol_code VARCHAR PRIMARY KEY,
    protocol_name_de VARCHAR NOT NULL,
    required_fields_de VARCHAR NOT NULL,
    protocol_description_de VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_handoff_route (
    route_code VARCHAR PRIMARY KEY,
    source_role_code VARCHAR NOT NULL,
    target_role_code VARCHAR NOT NULL,
    protocol_code VARCHAR NOT NULL,
    trigger_de VARCHAR NOT NULL,
    route_description_de VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_uncertainty_rule (
    rule_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    uncertainty_level VARCHAR NOT NULL,
    rule_text_de VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_source_binding (
    binding_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    binding_purpose_de VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_language_package_binding (
    binding_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    package_code VARCHAR NOT NULL,
    source_language_code VARCHAR NOT NULL,
    target_language_code VARCHAR NOT NULL,
    country_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR NOT NULL,
    binding_purpose_de VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);