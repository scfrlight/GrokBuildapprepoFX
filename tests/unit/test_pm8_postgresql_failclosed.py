"""PostgreSQL fail-closed tests. No live server required."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from botmoduleproject1.app.secrets import SECRET_ALLOWLIST, secrets_from_environ
from botmoduleproject1.app.settings import Pm8PersistenceSection
from botmoduleproject1.modules.pm8_persistence.postgres.dsn import PostgresDsnError, redact_dsn, validate_postgres_dsn
from botmoduleproject1.modules.pm8_persistence.store import StorageUnavailable, open_pm8_store

ROOT = Path(__file__).resolve().parents[2]


def test_postgresql_mode_without_dsn_raises_and_does_not_open_sqlite():
    with pytest.raises(StorageUnavailable, match="BOTMODULEPROJECT1_DATABASE_URL"):
        open_pm8_store(mode="postgresql", dsn=None, path=":memory:")


def test_postgresql_mode_refuses_sqlite_dsn():
    with pytest.raises(StorageUnavailable, match="sqlite"):
        open_pm8_store(mode="postgresql", dsn="sqlite:///tmp/pm8.sqlite")


def test_postgresql_unavailable_host_fails_closed():
    with pytest.raises(StorageUnavailable, match="unavailable"):
        open_pm8_store(mode="postgresql", dsn="postgresql://pm8@127.0.0.1:1/pm8_test", connect_timeout=1)


def test_unprefixed_database_url_is_ignored():
    assert "DATABASE_URL" not in SECRET_ALLOWLIST
    mapped = secrets_from_environ(
        {
            "DATABASE_URL": "postgresql://attacker@evil/db",
            "BOTMODULEPROJECT1_DATABASE_URL": "",
        }
    )
    assert "persistence" not in mapped


def test_allowlisted_dsn_is_mapped():
    mapped = secrets_from_environ({"BOTMODULEPROJECT1_DATABASE_URL": "postgresql://pm8@127.0.0.1:55432/pm8_test"})
    assert mapped["persistence"]["dsn"].startswith("postgresql://")


def test_operating_mode_accepts_postgresql_and_refuses_production_durable():
    section = Pm8PersistenceSection(operating_mode="postgresql")
    assert section.operating_mode == "postgresql"
    assert section.production_durable is False
    with pytest.raises(ValidationError):
        Pm8PersistenceSection(production_durable=True)
    with pytest.raises(ValidationError):
        Pm8PersistenceSection(operating_mode="production_durable")


def test_dsn_validation_and_redaction():
    with pytest.raises(PostgresDsnError):
        validate_postgres_dsn("")
    with pytest.raises(PostgresDsnError):
        validate_postgres_dsn("mysql://x")
    dsn = "postgresql://pm8:super-secret@127.0.0.1:55432/pm8_test"
    redacted = redact_dsn(dsn)
    assert "super-secret" not in redacted
    assert "pm8" in redacted
    assert "127.0.0.1" in redacted


def test_ci_wires_postgres_service_and_prefixed_dsn():
    yml = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "postgres:" in yml
    assert "BOTMODULEPROJECT1_DATABASE_URL" in yml
    assert "postgres:16" in yml
    assert "DATABASE_URL:" not in yml or "BOTMODULEPROJECT1_DATABASE_URL" in yml


def test_postgresql_docs_exist():
    for rel in (
        "docs/PM8_POSTGRESQL_DURABILITY.md",
        "docs/guides/postgres_setup.md",
        "docs/guides/transaction_boundaries.md",
        "docs/guides/migration_policy.md",
        "docs/runbooks/pm8_postgres_recovery.md",
        "docs/runbooks/pm8_postgres_reconciliation.md",
    ):
        assert (ROOT / rel).is_file(), rel
    matrix = (ROOT / "docs" / "TRACEABILITY_MATRIX.md").read_text(encoding="utf-8")
    for row in ("PG-01", "PG-08", "PG-12"):
        assert row in matrix
