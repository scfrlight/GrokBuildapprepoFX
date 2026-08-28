"""Event identity fields shared by inter-module messages."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from botmoduleproject1.contracts.v1.time import ensure_aware_utc, utc_now

SCHEMA_VERSION: Literal["v1"] = "v1"


class ContractModel(BaseModel):
    """Frozen v1 value object. Extra fields are rejected."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["v1"] = SCHEMA_VERSION


class EventEnvelope(ContractModel):
    """Envelope required on inter-module facts and commands."""

    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now)
    event_type: str
    producer: str
    payload_type: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @field_validator("event_type", "producer")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped


def identified_defaults() -> dict[str, Any]:
    return {
        "event_id": uuid4(),
        "correlation_id": uuid4(),
        "occurred_at": utc_now(),
    }
