from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "Database" / "Migrations"


def test_initial_migrations_are_present():
    assert (MIGRATIONS / "0001_system_schema.sql").exists()
    assert (MIGRATIONS / "0002_audit_foundation.sql").exists()


def test_migrations_do_not_target_legacy_folder():
    assert "08_Migration" not in str(MIGRATIONS)


def test_migration_sql_contains_audit_foundation():
    sql = (MIGRATIONS / "0002_audit_foundation.sql").read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS alin_audit" in sql
    assert "CREATE TABLE IF NOT EXISTS alin_audit.audit_events" in sql
