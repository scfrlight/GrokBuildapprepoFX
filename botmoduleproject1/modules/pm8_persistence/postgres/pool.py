"""Bounded connection helper. One transactional connection plus extras for workers."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row


def connect(
    dsn: str,
    *,
    connect_timeout: int = 5,
    statement_timeout_ms: int = 30_000,
    application_name: str = "pm8_persistence",
    autocommit: bool = True,
    options: str | None = None,
) -> psycopg.Connection[Any]:
    conn = psycopg.connect(
        dsn,
        autocommit=autocommit,
        connect_timeout=connect_timeout,
        application_name=application_name,
        row_factory=dict_row,
        options=options or f"-c statement_timeout={int(statement_timeout_ms)}",
    )
    return conn
