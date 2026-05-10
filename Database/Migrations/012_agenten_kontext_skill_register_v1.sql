-- Grundgerüst für Agenten-Kontext- und Skill-Register
-- Erstellt Tabellen für Rollen, Skills, Zuständigkeitsregeln,
-- Übergabeprotokolle, Unsicherheitsregeln sowie Quellen- und Sprachpaketbindungen.

CREATE TABLE IF NOT EXISTS agent_role_registry (
    role_code VARCHAR PRIMARY KEY,
    role_name_de VARCHAR NOT NULL,
    role_description_de VARCHAR,
    specialist_area_code VARCHAR,
    country_code VARCHAR,
    language_code VARCHAR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_skill_registry (
    skill_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    skill_name_de VARCHAR NOT NULL,
    skill_description_de VARCHAR,
    skill_type VARCHAR DEFAULT 'fachlich',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_scope_rule (
    rule_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR NOT NULL,
    country_code VARCHAR,
    language_code VARCHAR,
    scope_type VARCHAR DEFAULT 'zuständig',
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_handoff_protocol (
    protocol_code VARCHAR PRIMARY KEY,
    from_role_code VARCHAR NOT NULL,
    to_role_code VARCHAR NOT NULL,
    handoff_reason VARCHAR,
    required_fields VARCHAR,
    response_required BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_handoff_route (
    route_code VARCHAR PRIMARY KEY,
    from_role_code VARCHAR NOT NULL,
    to_role_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR,
    country_code VARCHAR,
    language_code VARCHAR,
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_uncertainty_rule (
    rule_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    uncertainty_level VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    action_detail_de VARCHAR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_source_binding (
    binding_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    binding_type VARCHAR DEFAULT 'primär',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_language_package_binding (
    binding_code VARCHAR PRIMARY KEY,
    role_code VARCHAR NOT NULL,
    package_code VARCHAR NOT NULL,
    binding_type VARCHAR DEFAULT 'primär',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
