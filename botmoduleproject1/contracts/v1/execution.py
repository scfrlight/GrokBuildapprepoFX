"""Order, position, and execution report contracts (PM5).

Sequence 07 extends this module backward-compatibly. Existing OrderRequest /
OrderStatus / ExecutionReport remain. New OMS/EMS types do not replace them.
PM5 output is not a live broker order in Sequence 07.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

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


class ExecutionMode(str, Enum):
    DISABLED = "disabled"
    SHADOW = "shadow"
    SIMULATION = "simulation"
    DEMO_CANDIDATE = "demo_candidate"
    DEMO_ENABLED = "demo_enabled"
    LIVE = "live"


class ExecutionLifecycleState(str, Enum):
    INTENT_CREATED = "intent_created"
    VALIDATED = "validated"
    BLOCKED = "blocked"
    QUEUED = "queued"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    MODIFY_REQUESTED = "modify_requested"
    MODIFIED = "modified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    RECONCILIATION_PENDING = "reconciliation_pending"
    RECONCILED = "reconciled"
    MISMATCH_DETECTED = "mismatch_detected"
    RECOVERY_PENDING = "recovery_pending"
    RECOVERED = "recovered"
    FROZEN = "frozen"


class ExecutionRejectReason(str, Enum):
    MISSING_AUTHORIZATION = "missing_authorization"
    PM4_DENY = "pm4_deny"
    EXECUTION_NOT_PERMITTED = "execution_not_permitted"
    STALE_INTENT = "stale_intent"
    LOOKAHEAD = "lookahead"
    SCHEMA_MISMATCH = "schema_mismatch"
    UNSUPPORTED_SYMBOL = "unsupported_symbol"
    UNSUPPORTED_SIDE = "unsupported_side"
    INVALID_QUANTITY = "invalid_quantity"
    QUANTITY_EXCEEDS_PM4 = "quantity_exceeds_pm4"
    INVALID_ORDER_TYPE = "invalid_order_type"
    MISSING_TRACE = "missing_trace"
    DUPLICATE_CONFLICT = "duplicate_conflict"
    KILL_SWITCH = "kill_switch"
    CONTROL_BLOCKED = "control_blocked"
    FEATURE_DISABLED = "feature_disabled"
    BROKER_UNAVAILABLE = "broker_unavailable"
    MODE_DISABLED = "mode_disabled"
    LIVE_BLOCKED = "live_blocked"
    SESSION_NOT_EXECUTABLE = "session_not_executable"
    RECONCILIATION_CRITICAL = "reconciliation_critical"
    THROTTLED = "throttled"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    ADAPTER_DISABLED = "adapter_disabled"


class ReconciliationOutcome(str, Enum):
    PASS = "pass"
    MISMATCH = "mismatch"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class Pm5OperatingState(str, Enum):
    NORMAL = "normal"
    THROTTLED = "throttled"
    DEGRADED = "degraded"
    RECONCILIATION_WARNING = "reconciliation_warning"
    RECONCILIATION_CRITICAL = "reconciliation_critical"
    CLOSE_ONLY = "close_only"
    FREEZE_NEW_ORDERS = "freeze_new_orders"
    EMERGENCY_CANCEL = "emergency_cancel"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    ORDERLY_WITHDRAWAL = "orderly_withdrawal"
    RECOVERY_REPLAY = "recovery_replay"
    RECOVERED = "recovered"


class ControlActionType(str, Enum):
    CANCEL_ORDER = "cancel_order"
    CANCEL_GROUP = "cancel_group"
    CANCEL_ALL = "cancel_all"
    BLOCK_NEW = "block_new"
    FREEZE = "freeze"
    CLOSE_ONLY = "close_only"
    NO_NEW_RISK = "no_new_risk"
    EMERGENCY_CANCEL = "emergency_cancel"
    MANUAL_REVIEW = "manual_review"
    RECOVERY_REQUEST = "recovery_request"
    REENABLE = "reenable"


class ControlScope(str, Enum):
    SYMBOL = "symbol"
    STRATEGY = "strategy"
    CLUSTER = "cluster"
    ACCOUNT = "account"
    GLOBAL = "global"


class BrokerEventType(str, Enum):
    DISABLED = "disabled"
    SIMULATED_ACK = "simulated_ack"
    SIMULATED_FILL = "simulated_fill"
    SIMULATED_CANCEL = "simulated_cancel"
    SIMULATED_REJECT = "simulated_reject"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    ERROR = "error"


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
    outcome: ReconciliationOutcome = ReconciliationOutcome.DEGRADED
    mismatch_type: str | None = None
    severity: str = "medium"
    local_state: dict[str, Any] = Field(default_factory=dict)
    broker_state: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = "no_broker_truth_available"
    remediation_status: str = "pending"
    broker_truth_available: bool = False

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class NormalizedExecutionCommand(ContractModel):
    command_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    pm4_decision_id: UUID
    symbol: str
    direction: Direction
    approved_quantity: Decimal
    requested_quantity: Decimal
    order_type: str
    entry_price: Decimal | None = None
    stop_price: Decimal | None = None
    slippage_tolerance: Decimal = Decimal("0")
    expiry: datetime | None = None
    urgency: str = "normal"
    execution_policy: str = "simulation_only"
    route_restrictions: tuple[str, ...] = ("broker_closed",)
    idempotency_key: str
    correlation_id: UUID
    causation_id: UUID | None = None
    broker_eligible: bool = False

    @model_validator(mode="after")
    def _qty(self) -> NormalizedExecutionCommand:
        if self.requested_quantity > self.approved_quantity:
            raise ValueError("PM5 cannot request quantity above PM4 approved size")
        if self.requested_quantity < 0 or self.approved_quantity < 0:
            raise ValueError("quantity must be >= 0")
        return self


class OrderLifecycleEvent(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    occurred_at: datetime
    from_state: ExecutionLifecycleState | None = None
    to_state: ExecutionLifecycleState
    reason: str
    actor: str
    source: str
    correlation_id: UUID | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class OrderRecord(ContractModel):
    order_id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    pm4_decision_id: UUID
    idempotency_key: str
    correlation_id: UUID
    causation_id: UUID | None = None
    occurred_at: datetime
    symbol: str
    direction: Direction
    entry_type: EntryType
    original_quantity: Decimal
    remaining_quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    state: ExecutionLifecycleState
    broker_ticket: str | None = None
    broker_side_effect: bool = False
    simulation: bool = True
    stop_price: Decimal | None = None
    entry_price: Decimal | None = None
    average_fill_price: Decimal | None = None
    reject_reason: ExecutionRejectReason | None = None
    detail: str = ""

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class BrokerAckEvent(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    occurred_at: datetime
    kind: BrokerEventType
    ticket: str | None = None
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class FillEvent(ContractModel):
    fill_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    occurred_at: datetime
    quantity: Decimal
    price: Decimal
    source: str = "simulation"
    ticket: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ControlActionRecord(ContractModel):
    action_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    action: ControlActionType
    scope: ControlScope
    scope_id: str | None = None
    actor: str
    reason: str
    trigger_source: str
    affected_order_ids: tuple[UUID, ...] = ()
    result: str = "applied"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class SurveillanceAlert(ContractModel):
    alert_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    severity: str
    category: str
    detector: str
    observed: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    scope: str
    trace_id: UUID | None = None
    recommended_action: str
    automatic_protection: bool = False

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ExecutionQualityReport(ContractModel):
    as_of: datetime
    decision_to_submit_ms: Decimal | None = None
    submit_to_ack_ms: Decimal | None = None
    ack_to_fill_ms: Decimal | None = None
    total_completion_ms: Decimal | None = None
    realized_slippage: Decimal | None = None
    reject_rate: Decimal | None = None
    partial_fill_ratio: Decimal | None = None
    cancel_ratio: Decimal | None = None
    success_rate: Decimal | None = None
    sample_size: int = 0
    data_status: str = "insufficient_data"
    dimensions: dict[str, Any] = Field(default_factory=dict)

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class ExposureState(ContractModel):
    as_of: datetime
    working_orders: int = 0
    open_positions: int = 0
    working_quantity: Decimal = Decimal("0")
    position_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal = Decimal("0")
    expected_exposure: Decimal = Decimal("0")
    broker_exposure: Decimal | None = None
    exposure_delta: Decimal | None = None
    reconciliation_status: ReconciliationOutcome = ReconciliationOutcome.DEGRADED
    last_broker_refresh: datetime | None = None
    stale: bool = True
    broker_truth_available: bool = False

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class ExecutionIntentReceipt(ContractModel):
    accepted: bool
    order_id: UUID | None = None
    state: ExecutionLifecycleState | None = None
    reasons: tuple[ExecutionRejectReason, ...] = ()
    detail: str = ""
    broker_side_effect: bool = False
    simulation: bool = True
    idempotent_replay: bool = False


class ReplayBundle(ContractModel):
    bundle_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    events: tuple[dict[str, Any], ...] = ()
    deterministic: bool = True


class ExecutionPublicationBundle(ContractModel):
    bundle_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    order: OrderRecord | None = None
    receipt: ExecutionIntentReceipt
    command: NormalizedExecutionCommand | None = None
    lifecycle: tuple[OrderLifecycleEvent, ...] = ()
    fills: tuple[FillEvent, ...] = ()
    control: tuple[ControlActionRecord, ...] = ()
    reconciliation: ReconciliationRecord | None = None
    exposure: ExposureState | None = None
    quality: ExecutionQualityReport | None = None
    alerts: tuple[SurveillanceAlert, ...] = ()
    operating_state: Pm5OperatingState = Pm5OperatingState.DEGRADED
    execution_mode: ExecutionMode = ExecutionMode.DISABLED
    broker_side_effect: bool = False
    mt5_used: bool = False
    durable: bool = False
    producer: str = "pm5_execution"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _no_live_send(self) -> ExecutionPublicationBundle:
        if self.mt5_used:
            raise ValueError("Sequence 07 forbids mt5_used=true")
        if self.broker_side_effect:
            raise ValueError("Sequence 07 forbids broker_side_effect=true")
        if self.execution_mode in {ExecutionMode.LIVE, ExecutionMode.DEMO_ENABLED}:
            raise ValueError("Sequence 07 forbids live/demo_enabled publication")
        return self
