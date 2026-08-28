"""PM4 risk-gate contracts. Exclusive execution permission (ADR-007)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class RiskVerdictStatus(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    HALT = "halt"


class RiskRejectionReason(str, Enum):
    ENGINE_UNAVAILABLE = "engine_unavailable"
    NOT_READY = "not_ready"
    LIVE_DISABLED = "live_disabled"
    EXPOSURE_LIMIT = "exposure_limit"
    DRAWDOWN_LIMIT = "drawdown_limit"
    STALE_DATA = "stale_data"
    LEDGER_INCONSISTENT = "ledger_inconsistent"
    KILL_SWITCH = "kill_switch"
    INVALID_INTENT = "invalid_intent"
    POLICY = "policy"
    UNKNOWN_STATE = "unknown_state"


class ExposureSnapshot(ContractModel):
    as_of: datetime
    gross_notional: Decimal = Decimal("0")
    net_notional: Decimal = Decimal("0")
    open_position_count: int = Field(default=0, ge=0)
    heat_r: Decimal = Decimal("0")

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class RiskVerdict(ContractModel):
    """Sole final permission object consumed by PM5."""

    verdict_id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    occurred_at: datetime
    status: RiskVerdictStatus
    reasons: tuple[RiskRejectionReason, ...] = ()
    detail: str | None = None
    expires_at: datetime | None = None
    producer: str = "pm4_risk"

    @field_validator("occurred_at", "expires_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)

    @property
    def allows_execution(self) -> bool:
        return self.status is RiskVerdictStatus.ALLOW
