"""PostgreSQL backend for PM8 Persistence, Ledger & Recovery Engine.

Not a second persistence product. Swappable behind PersistenceApiV1.
Fails closed when PostgreSQL is configured but unavailable.
Never falls back to SQLite or memory.
"""

from botmoduleproject1.modules.pm8_persistence.postgres.dsn import (
    PostgresDsnError,
    redact_dsn,
    validate_postgres_dsn,
)
from botmoduleproject1.modules.pm8_persistence.postgres.store import PostgresStore

__all__ = [
    "PostgresStore",
    "PostgresDsnError",
    "redact_dsn",
    "validate_postgres_dsn",
]
