"""Journal / evidence contracts (PM7)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class EventType(str, Enum):
    LIFECYCLE = "lifecycle"
    CONFIG = "config"
    INTENT = "intent"
    FORECAST = "forecast"
    RISK = "risk"
    ORDER = "order"
    FILL = "fill"
    ALERT = "alert"
    APPROVAL = "approval"
    TUNING = "tuning"
    HALT = "halt"
    DIAGNOSTIC = "diagnostic"


class JournalEntry(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    occurred_at: datetime
    event_type: EventType
    producer: str
    summary: str
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
