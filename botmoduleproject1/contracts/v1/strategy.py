"""PM3-Strategy Engine contracts.

This namespace is the Strategy Engine. Do not import forecasting types here.
A TradeIntent is not an order and cannot authorize execution.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

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
    """v1 kept ACCEPT/REJECT/ABSTAIN; Sequence 04 adds directional outcomes."""

    ACCEPT = "accept"
    REJECT = "reject"
    ABSTAIN = "abstain"
    GO_LONG = "go_long"
    GO_SHORT = "go_short"
    WAIT = "wait"
    NO_TRADE = "no_trade"


class StopType(str, Enum):
    HARD = "hard"
    STRUCTURE = "structure"
    ATR = "atr"
    TIME = "time"
    NONE = "none"


class UrgencyClass(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXPIRE_SOON = "expire_soon"


class NoTradeDecision(ContractModel):
    symbol: str
    reason: str
    as_of: datetime
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    observe_only: bool = True
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    producer: str = "pm3_strategy_engine"

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class ExitPlan(ContractModel):
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    time_stop_seconds: int | None = Field(default=None, ge=1)
    notes: str | None = None
    stop_type: StopType = StopType.ATR
    stop_price: Decimal | None = None
    tp_plan: str | None = None
    trail_plan: str | None = None
    time_stop_plan: str | None = None


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
    profile_id: str | None = None
    version_id: str | None = None
    entry_zone_low: Decimal | None = None
    entry_zone_high: Decimal | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    setup_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    consensus_score: float = Field(default=0.0, ge=0.0, le=1.0)
    regime_state: str | None = None
    urgency_class: UrgencyClass = UrgencyClass.NORMAL
    signal_expiry: datetime | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    source_candidate_id: UUID | None = None
    pm2_rank: int | None = None
    created_at: datetime | None = None

    @field_validator("occurred_at", "signal_expiry", "created_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)

    @field_validator("idempotency_key")
    @classmethod
    def _key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency_key is required on TradeIntent")
        return value

    @model_validator(mode="after")
    def _no_lot_size(self) -> TradeIntent:
        if self.requested_volume is not None:
            raise ValueError(
                "TradeIntent must not carry lot size; requested_volume must be None"
            )
        return self
