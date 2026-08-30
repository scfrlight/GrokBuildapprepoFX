"""Canonical Sequence 09 — PM8 consolidated persistence contracts.

Versioned API types. Downstream modules must not reach repositories.
Committed records are immutable. SIM-* / DEMO-* are never broker truth.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class PersistenceApiVersion(str, Enum):
    V1 = "v1"


class TableFamily(str, Enum):
    EVENT = "event"
    SIGNAL = "signal"
    ORDER = "order"
    EXECUTION = "execution"
    RELIABILITY = "reliability"
    RECOVERY = "recovery"
    PROJECTION = "projection"
    RECONCILIATION = "reconciliation"
    AUDIT = "audit"


class IdempotencyEdge(str, Enum):
    REQUEST = "request"
    EVENT_CONSUMER = "event_consumer"
    BROKER_CALLBACK = "broker_callback"
    PROJECTION = "projection"


class OutboxState(str, Enum):
    PENDING = "pending"
    DISPATCHING = "dispatching"
    PUBLISHED = "published"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class InboxState(str, Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    QUARANTINED = "quarantined"


class RepairAction(str, Enum):
    NONE = "none"
    CORRECTION_EVENT = "correction_event"
    QUARANTINE = "quarantine"
    HALT = "halt"
    REFUSED_REWRITE = "refused_rewrite"


class ApiDisposition(str, Enum):
    COMMITTED = "committed"
    DUPLICATE_IGNORED = "duplicate_ignored"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    DEGRADED = "degraded"
    FEATURE_DISABLED = "feature_disabled"
    COMPROMISED = "compromised"


class PersistRecord(ContractModel):
    record_id: UUID = Field(default_factory=uuid4)
    family: TableFamily
    occurred_at: datetime
    idempotency_key: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    truth_source: str = "unknown"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ApiResult(ContractModel):
    disposition: ApiDisposition
    api_version: PersistenceApiVersion = PersistenceApiVersion.V1
    record_id: UUID | None = None
    sequence_no: int | None = None
    duplicate_of: UUID | None = None
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class IntegrityFinding(ContractModel):
    state: str
    sequence_from: int = 0
    sequence_to: int = 0
    mismatch_at: int | None = None
    message: str = ""


class BackupReport(ContractModel):
    backup_id: UUID
    checksum: str
    path: str
    verified: bool
    event_count: int
    created_at: datetime
