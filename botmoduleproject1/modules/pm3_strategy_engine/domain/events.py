"""Typed lifecycle events (audit-ready, in-memory)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.contracts.v1.strategy_engine import ProfileChangeAction, StrategyEventType
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from pydantic import field_validator


class StrategyLifecycleEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    event_type: StrategyEventType
    action: ProfileChangeAction | None = None
    profile_id: str | None = None
    version_id: str | None = None
    symbol: str | None = None
    summary: str
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
