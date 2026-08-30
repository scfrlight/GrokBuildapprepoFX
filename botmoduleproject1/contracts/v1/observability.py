"""Sequence 14 observability contracts. Not a trading path."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import UTC, ensure_aware_utc, utc_now


class ProbeState(str, Enum):
    PASS = "pass"
    DEGRADED = "degraded"
    FAIL = "fail"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class HealthDimension(str, Enum):
    LIVENESS = "liveness"
    READINESS = "readiness"
    OPERATIONAL_HEALTH = "operational_health"
    TRADING_READINESS = "trading_readiness"
    RECOVERY_READINESS = "recovery_readiness"
    PERSISTENCE_READINESS = "persistence_readiness"
    BROKER_VENUE = "broker_venue_availability"
    OPERATOR_READINESS = "operator_readiness"


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricUnit(str, Enum):
    COUNT = "count"
    MILLISECONDS = "milliseconds"
    SECONDS = "seconds"
    RATIO = "ratio"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCode(str, Enum):
    CONFIGURATION_ERROR = "configuration_error"
    UNSUPPORTED_PYTHON_VERSION = "unsupported_python_version"
    VALIDATION_ERROR = "validation_error"
    CONTRACT_ERROR = "contract_error"
    STALE_DATA_ERROR = "stale_data_error"
    PERSISTENCE_ERROR = "persistence_error"
    INTEGRITY_ERROR = "integrity_error"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    DUPLICATE_EVENT = "duplicate_event"
    DUPLICATE_EXECUTION = "duplicate_execution"
    BROKER_UNAVAILABLE = "broker_unavailable"
    BROKER_REJECTED = "broker_rejected"
    RECONCILIATION_MISMATCH = "reconciliation_mismatch"
    PROJECTION_ERROR = "projection_error"
    RECOVERY_ERROR = "recovery_error"
    PERMISSION_DENIED = "permission_denied"
    UNSAFE_OPERATION = "unsafe_operation"
    SECRET_HANDLING_ERROR = "secret_handling_error"
    UNEXPECTED_INTERNAL_ERROR = "unexpected_internal_error"


class DimensionStatus(ContractModel):
    dimension: HealthDimension
    state: ProbeState
    reason: str
    trading_halt: bool = False
    source: str = "observability"


class HealthReport(ContractModel):
    """Operational health across separated dimensions. Not a single boolean."""

    captured_at: datetime = Field(default_factory=utc_now)
    liveness: ProbeState
    operational_health: ProbeState
    dimensions: tuple[DimensionStatus, ...]
    trading_readiness: bool
    trading_halted: bool
    stale_data: bool
    venue_present: bool
    recovery_complete: bool
    flags_any_on: bool
    reasons: tuple[str, ...] = ()

    @field_validator("captured_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "captured_at")


class ReadinessReport(ContractModel):
    """Separated readiness. Alive does not imply ready. Ready does not imply trade."""

    captured_at: datetime = Field(default_factory=utc_now)
    process_alive: bool
    accept_observe: bool
    accept_trade: bool
    liveness: ProbeState
    readiness: ProbeState
    trading_readiness: ProbeState
    recovery_readiness: ProbeState
    persistence_readiness: ProbeState
    broker_venue: ProbeState
    operator_readiness: ProbeState
    reasons: tuple[str, ...] = ()

    @field_validator("captured_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "captured_at")


class StructuredLogEvent(ContractModel):
    timestamp: datetime = Field(default_factory=utc_now)
    level: LogLevel
    event_name: str
    module: str
    sequence: int
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    trace_id: UUID = Field(default_factory=uuid4)
    actor: str = "system"
    profile: str
    symbol: str | None = None
    status: str
    error_code: ErrorCode | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "timestamp")

    @field_validator("event_name", "module", "actor", "profile", "status")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped


class MetricSpec(ContractModel):
    name: str
    metric_type: MetricType
    unit: MetricUnit
    labels: tuple[str, ...]
    cardinality: str
    source_module: str
    update_point: str
    safe_default: float
    description: str


class MetricSample(ContractModel):
    name: str
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=utc_now)

    @field_validator("captured_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "captured_at")


class ErrorSpec(ContractModel):
    code: ErrorCode
    severity: ErrorSeverity
    retryable: bool
    operator_action: str
    system_action: str
    trading_must_halt: bool
    audit_required: bool
    public_safe_message: str


class Runbook(ContractModel):
    runbook_id: str
    title: str
    trigger: str
    symptoms: tuple[str, ...]
    safety_classification: str
    automatic_system_behavior: str
    operator_inspection_commands: tuple[str, ...]
    prohibited_operator_actions: tuple[str, ...]
    recovery_steps: tuple[str, ...]
    verification_steps: tuple[str, ...]
    rollback_steps: tuple[str, ...]
    evidence_to_preserve: tuple[str, ...]
    closure_criteria: str
    escalation_criteria: str
    executable_check: str


class ObservabilitySnapshot(ContractModel):
    captured_at: datetime = Field(default_factory=utc_now)
    schema_version: Literal["v1"] = "v1"
    sequence: Literal[14] = 14
    health: HealthReport
    readiness: ReadinessReport
    metrics: tuple[MetricSample, ...]
    metric_catalog_count: int
    runbook_count: int
    error_catalog_count: int
    flags: dict[str, bool]
    live_trading_enabled: bool
    telegram_bound: bool
    python: str
    kernel_note: str = "NOT TRADE READY. Sequence 14 is observe-only."

    @field_validator("captured_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "captured_at")


ALLOWED_LOG_SYMBOLS = frozenset({"EURUSD", "GBPUSD", "USDJPY"})
ALLOWED_METRIC_LABELS = frozenset(
    {
        "module",
        "profile",
        "dimension",
        "error_code",
        "family",
        "outcome",
        "probe",
    }
)
FORBIDDEN_LABEL_FRAGMENTS = (
    "password",
    "token",
    "secret",
    "payload",
    "stack",
    "dsn",
    "authorization",
)

REQUIRED_LOG_FIELDS = (
    "timestamp",
    "level",
    "event_name",
    "module",
    "sequence",
    "correlation_id",
    "causation_id",
    "trace_id",
    "actor",
    "profile",
    "symbol",
    "status",
    "error_code",
    "metadata",
)


def utc_iso(value: datetime | None = None) -> str:
    stamp = value or utc_now()
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return stamp.astimezone(UTC).isoformat()
