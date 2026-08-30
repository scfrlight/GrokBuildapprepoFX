"""Outbox publisher protocol and local/test relay.

SQLite relay is local/test-only; PostgreSQL is required for production
multi-worker concurrency. No broker SDK inside PM8.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class OutboxPublisher(Protocol):
    def publish(self, row: dict[str, Any]) -> None: ...


class InProcessPublisher:
    """Deterministic in-process publisher for tests. Never a venue."""

    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []
        self.fail_next: int = 0
        self.fail_ids: set[str] = set()

    def publish(self, row: dict[str, Any]) -> None:
        oid = str(row.get("outbox_id"))
        if oid in self.fail_ids:
            raise RuntimeError("injected publish failure")
        if self.fail_next > 0:
            self.fail_next -= 1
            raise RuntimeError("injected publish failure")
        self.published.append(dict(row))
