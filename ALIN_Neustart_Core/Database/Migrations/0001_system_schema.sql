-- Phase 0, AP 0.2: System-Schema fuer Migrationen und Metadaten.
CREATE SCHEMA IF NOT EXISTS alin_system;

CREATE TABLE IF NOT EXISTS alin_system.schema_migrations (
    migration_id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    checksum_sha256 VARCHAR NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    applied_by VARCHAR NOT NULL,
    execution_ms BIGINT NOT NULL,
    status VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS alin_system.database_metadata (
    key VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

DELETE FROM alin_system.database_metadata
WHERE key IN ('database_name', 'schema_baseline', 'internet_policy');

INSERT INTO alin_system.database_metadata (key, value)
VALUES
    ('database_name', 'ALIN local DuckDB'),
    ('schema_baseline', 'phase0_ap02'),
    ('internet_policy', 'offline_first_no_foreign_api');
