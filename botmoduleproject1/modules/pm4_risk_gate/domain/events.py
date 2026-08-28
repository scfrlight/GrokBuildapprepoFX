"""Typed risk events mapped onto journal contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from botmoduleproject1.contracts.v1.journal import EventType, JournalEntry
from botmoduleproject1.contracts.v1.risk import RiskEventType
from botmoduleproject1.modules.pm4_risk_gate.domain.policies import PRODUCER


def risk_journal(
    *,
    occurred_at: datetime,
    kind: RiskEventType,
    summary: str,
    correlation_id: UUID,
    causation_id: UUID | None = None,
    idempotency_key: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> JournalEntry:
    event_type = EventType.HALT if kind is RiskEventType.KILL_SWITCH else EventType.RISK
    if kind is RiskEventType.INCIDENT:
        event_type = EventType.ALERT
    return JournalEntry(
        correlation_id=correlation_id,
        causation_id=causation_id,
        idempotency_key=idempotency_key,
        occurred_at=occurred_at,
        event_type=event_type,
        producer=PRODUCER,
        summary=summary,
        attributes={"risk_event": kind.value, **(attributes or {})},
    )
