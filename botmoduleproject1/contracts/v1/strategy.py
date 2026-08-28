"""PM3-Strategy Engine contracts.

This namespace is the Strategy Engine. Do not import forecasting types here.
A TradeIntent is not an order and cannot authorize execution.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class Direction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    FLAT = "flat"


class EntryType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class ConsensusDecision(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    ABSTAIN = "abstain"


class NoTradeDecision(ContractModel):
    symbol: str
    reason: str
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class ExitPlan(ContractModel):
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    time_stop_seconds: int | None = Field(default=None, ge=1)
    notes: str | None = None


class TradeIntent(ContractModel):
    """Hypothesis produced by the PM3-Strategy Engine. Not executable alone."""

    intent_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str
    occurred_at: datetime
    symbol: str
    direction: Direction
    entry_type: EntryType
    requested_volume: Decimal | None = None
    entry_price: Decimal | None = None
    exit_plan: ExitPlan | None = None
    consensus: ConsensusDecision = ConsensusDecision.ABSTAIN
    producer: str = "pm3_strategy_engine"
    thesis: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @field_validator("idempotency_key")
    @classmethod
    def _key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency_key is required on TradeIntent")
        return value
