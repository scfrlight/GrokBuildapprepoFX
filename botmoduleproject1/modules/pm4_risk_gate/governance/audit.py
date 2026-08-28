from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from botmoduleproject1.contracts.v1.journal import JournalEntry
from botmoduleproject1.contracts.v1.risk import RiskEventType
from botmoduleproject1.modules.pm4_risk_gate.domain.events import risk_journal


class AuditRecorder:
    def __init__(self) -> None:
        self.entries: list[JournalEntry] = []

    def record(
        self,
        *,
        occurred_at: datetime,
        kind: RiskEventType,
        summary: str,
        correlation_id: UUID,
        causation_id: UUID | None = None,
        idempotency_key: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> JournalEntry:
        entry = risk_journal(
            occurred_at=occurred_at,
            kind=kind,
            summary=summary,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            attributes=attributes,
        )
        self.entries.append(entry)
        return entry

    def summary(self) -> dict[str, Any]:
        return {
            "count": len(self.entries),
            "last": self.entries[-1].summary if self.entries else None,
            "durable": False,
        }
