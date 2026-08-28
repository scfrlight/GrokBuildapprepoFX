"""Order, position, and execution report contracts (PM5)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class OrderStatus(str, Enum):
    NEW = "new"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderRequest(ContractModel):
    """Execution request. Invalid without a RiskVerdict reference (ADR-007)."""

    order_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID
    idempotency_key: str
    occurred_at: datetime
    intent_id: UUID
    risk_verdict_id: UUID
    symbol: str
    direction: Direction
    entry_type: EntryType
    volume: Decimal
    price: Decimal | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @field_validator("idempotency_key")
    @classmethod
    def _key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("idempotency_key is required on OrderRequest")
        return value


class Position(ContractModel):
    position_id: UUID
    symbol: str
    direction: Direction
    volume: Decimal
    average_price: Decimal
    as_of: datetime
    broker_ticket: str | None = None

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class ExecutionReport(ContractModel):
    report_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    occurred_at: datetime
    order_id: UUID
    status: OrderStatus
    filled_volume: Decimal = Decimal("0")
    average_price: Decimal | None = None
    broker_ticket: str | None = None
    message: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ReconciliationRecord(ContractModel):
    record_id: UUID = Field(default_factory=uuid4)
    as_of: datetime
    consistent: bool
    ledger_position_count: int = Field(ge=0)
    broker_position_count: int = Field(ge=0)
    notes: str | None = None

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")
