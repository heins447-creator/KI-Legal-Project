CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id VARCHAR PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    note_de VARCHAR
);

CREATE TABLE IF NOT EXISTS de_specialist_area (
    specialist_area_code VARCHAR PRIMARY KEY,
    name_de VARCHAR NOT NULL,
    description_de VARCHAR,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS country_legal_area_mapping (
    mapping_code VARCHAR PRIMARY KEY,
    country_code VARCHAR NOT NULL,
    country_name_de VARCHAR NOT NULL,
    specialist_area_code VARCHAR NOT NULL,
    foreign_legal_area_name VARCHAR,
    legal_system_note_de VARCHAR,
    court_route_code VARCHAR,
    status VARCHAR DEFAULT 'vorbereitet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS country_court_route (
    route_code VARCHAR PRIMARY KEY,
    country_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR,
    court_system_name VARCHAR,
    route_description_de VARCHAR,
    first_instance VARCHAR,
    appeal_instance VARCHAR,
    highest_instance VARCHAR,
    status VARCHAR DEFAULT 'vorbereitet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS country_legal_profession (
    profession_code VARCHAR PRIMARY KEY,
    country_code VARCHAR NOT NULL,
    profession_name_native VARCHAR,
    profession_name_de VARCHAR,
    authority_or_bar VARCHAR,
    admission_note_de VARCHAR,
    specialist_equivalence_note_de VARCHAR,
    status VARCHAR DEFAULT 'vorbereitet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_registry (
    source_code VARCHAR PRIMARY KEY,
    source_name VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    jurisdiction VARCHAR,
    country_code VARCHAR,
    language_code VARCHAR,
    specialist_area_code VARCHAR,
    legal_area_native VARCHAR,
    source_rank INTEGER DEFAULT 0,
    update_status VARCHAR DEFAULT 'vorbereitet',
    cache_status VARCHAR DEFAULT 'nicht_geladen',
    offline_fallback VARCHAR DEFAULT 'nicht_vorhanden',
    url_hint VARCHAR,
    notes_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_adapter_registry (
    adapter_code VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    adapter_type VARCHAR DEFAULT 'manuell_vorgemerkt',
    endpoint_hint VARCHAR,
    auth_required BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT FALSE,
    notes_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_health_check (
    check_code VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    check_status VARCHAR DEFAULT 'nicht_geprueft',
    http_status INTEGER,
    checked_at TIMESTAMP,
    message_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_cache_policy (
    policy_code VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    cache_scope VARCHAR DEFAULT 'metadaten_und_auszuege',
    cache_ttl_seconds INTEGER DEFAULT 2592000,
    max_cache_size_mb INTEGER DEFAULT 100,
    offline_fallback_enabled BOOLEAN DEFAULT FALSE,
    retention_note_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_change_log (
    change_code VARCHAR PRIMARY KEY,
    source_code VARCHAR NOT NULL,
    change_type VARCHAR DEFAULT 'anlage',
    change_note_de VARCHAR,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS language_package_registry (
    package_code VARCHAR PRIMARY KEY,
    source_language_code VARCHAR NOT NULL,
    target_language_code VARCHAR NOT NULL,
    country_code VARCHAR NOT NULL,
    specialist_area_code VARCHAR NOT NULL,
    package_name VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'vorbereitet',
    context_rules_de VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS language_package_source_map (
    map_code VARCHAR PRIMARY KEY,
    package_code VARCHAR NOT NULL,
    source_code VARCHAR NOT NULL,
    source_role VARCHAR DEFAULT 'terminologie_oder_rechtsquelle',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);