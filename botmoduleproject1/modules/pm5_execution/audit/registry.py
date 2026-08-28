from __future__ import annotations

from datetime import datetime
from typing import Any

from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class AuditRegistry:
    """In-memory only. Not a durable ledger."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.incidents: list[dict[str, Any]] = []

    def record(self, *, now: datetime, kind: str, summary: str, **attrs: Any) -> dict[str, Any]:
        item = {
            "id": str(new_id()),
            "occurred_at": now.isoformat(),
            "kind": kind,
            "summary": summary,
            "durable": False,
            **attrs,
        }
        self.records.append(item)
        return item

    def incident(self, *, now: datetime, title: str, severity: str, detail: str) -> dict[str, Any]:
        item = {
            "incident_id": str(new_id()),
            "occurred_at": now.isoformat(),
            "title": title,
            "severity": severity,
            "detail": detail,
            "durable": False,
        }
        self.incidents.append(item)
        return item
