"""Pre-intent signal contracts. A signal is not an order."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class ConfluenceScore(ContractModel):
    value: float = Field(ge=0.0, le=1.0)
    components: dict[str, float] = Field(default_factory=dict)


class SignalEvent(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    occurred_at: datetime
    symbol: str
    direction: Direction
    confluence: ConfluenceScore
    producer: str

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
