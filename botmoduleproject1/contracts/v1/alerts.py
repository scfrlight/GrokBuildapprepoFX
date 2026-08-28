"""Alert and approval contracts (PM6 / PM9)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertEvent(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    occurred_at: datetime
    severity: AlertSeverity
    code: str
    message: str
    producer: str

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(ContractModel):
    """Operator approval is a command. It still cannot skip PM4."""

    request_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str
    occurred_at: datetime
    intent_id: UUID | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str
    note: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
