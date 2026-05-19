-- Phase 0, AP 0.2: Minimale Audit-Grundlage.
CREATE SCHEMA IF NOT EXISTS alin_audit;

CREATE TABLE IF NOT EXISTS alin_audit.audit_events (
    event_id VARCHAR PRIMARY KEY,
    event_time TIMESTAMP NOT NULL DEFAULT current_timestamp,
    actor_role VARCHAR NOT NULL,
    actor_id VARCHAR,
    action VARCHAR NOT NULL,
    target_type VARCHAR NOT NULL,
    target_id VARCHAR,
    source_module VARCHAR NOT NULL,
    details_json VARCHAR NOT NULL,
    created_by_runner VARCHAR NOT NULL
);
