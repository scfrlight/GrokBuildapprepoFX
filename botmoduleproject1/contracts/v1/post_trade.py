"""PM6 post-trade monitoring, surveillance, incident, and governance contracts.

Sequence 08. These types do not replace PM4 risk or PM5 execution contracts.
PM6 never creates orders. Simulation truth is never broker truth.
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


class TruthSource(str, Enum):
    LOCAL_OMS_TRUTH = "local_oms_truth"
    SIMULATION_TRUTH = "simulation_truth"
    BROKER_TRUTH = "broker_truth"
    RECONCILED_TRUTH = "reconciled_truth"
    UNRESOLVED_MISMATCH = "unresolved_mismatch"
    UNKNOWN = "unknown"
    STALE = "stale"


class IntakeDisposition(str, Enum):
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    DEGRADED = "degraded"
    REQUIRES_REVIEW = "requires_review"


class MonitoringState(str, Enum):
    HEALTHY = "healthy"
    WATCH = "watch"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    INCIDENT_ACTIVE = "incident_active"
    WITHDRAWAL_IN_PROGRESS = "withdrawal_in_progress"
    REVIEW_PENDING = "review_pending"
    STABILIZED = "stabilized"


class IncidentState(str, Enum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    CLASSIFIED = "classified"
    ESCALATED = "escalated"
    CONTAINMENT_IN_PROGRESS = "containment_in_progress"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    REVIEW_PENDING = "review_pending"
    CLOSED = "closed"
    TRANSFERRED_TO_PERSISTENCE = "transferred_to_persistence"


class IncidentCategory(str, Enum):
    TECHNICAL = "technical"
    EXECUTION = "execution"
    RECONCILIATION = "reconciliation"
    RISK_CONTROL = "risk_control"
    MONITORING = "monitoring"
    GOVERNANCE = "governance"
    OPERATOR = "operator"
    CONDUCT = "conduct"
    DATA_QUALITY = "data_quality"
    SECURITY = "security"
    RECOVERY = "recovery"


class IncidentType(str, Enum):
    POST_TRADE_CONTROL_BREACH = "post_trade_control_breach"
    MONITORING_ALERT_BURST = "monitoring_alert_burst"
    EXECUTION_ANOMALY = "execution_anomaly"
    RECONCILIATION_FOLLOWUP_REQUIRED = "reconciliation_followup_required"
    KILL_STATE_BREACH = "kill_state_breach"
    ORDERLY_WITHDRAWAL_REQUIRED = "orderly_withdrawal_required"
    MANUAL_OVERRIDE_INCIDENT = "manual_override_incident"
    AUDIT_EVIDENCE_GAP = "audit_evidence_gap"
    VALIDATION_GAP = "validation_gap"
    UNEXPECTED_TRADING_CONTINUATION = "unexpected_trading_continuation"
    STALE_MONITORING_DATA = "stale_monitoring_data"
    TRUTH_PROVENANCE_CONFLICT = "truth_provenance_conflict"
    REPEATED_EXECUTION_ANOMALY = "repeated_execution_anomaly"
    CONTROL_STATE_INCONSISTENCY = "control_state_inconsistency"


class SeverityLevel(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationRoute(str, Enum):
    IMMEDIATE = "immediate"
    SAME_SESSION = "same_session"
    SAME_DAY = "same_day"
    SCHEDULED_REVIEW = "scheduled_review"


class WithdrawalState(str, Enum):
    NOT_REQUIRED = "not_required"
    RECOMMENDED = "recommended"
    APPROVAL_PENDING = "approval_pending"
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"


class GovernanceReviewState(str, Enum):
    SCHEDULED = "scheduled"
    IN_REVIEW = "in_review"
    EVIDENCE_COMPILED = "evidence_compiled"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    REMEDIATION_REQUIRED = "remediation_required"
    CLOSED = "closed"


class LaneKind(str, Enum):
    OPERATOR = "operator"
    CONTROL = "control"


class ControlRequestKind(str, Enum):
    FREEZE = "freeze"
    CLOSE_ONLY = "close_only"
    NO_NEW_RISK = "no_new_risk"
    CANCEL_WORKING = "cancel_working"
    MANUAL_REVIEW = "manual_review"
    ORDERLY_WITHDRAWAL = "orderly_withdrawal"


class IntakeRecord(ContractModel):
    disposition: IntakeDisposition
    reasons: tuple[str, ...] = ()
    detail: str = ""
    source: str = "pm6_post_trade"
    event_id: UUID | None = None
    trace_id: UUID | None = None
    occurred_at: datetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value, "occurred_at")


class LaneSummary(ContractModel):
    lane: LaneKind
    as_of: datetime
    priority: SeverityLevel
    headline: str
    items: tuple[str, ...] = ()
    recommended_action: str = "observe"
    incident_count: int = 0
    alert_count: int = 0

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class PostTradeAlert(ContractModel):
    """PM6 surveillance alert. Distinct from PM5 Execution SurveillanceAlert."""

    alert_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    created_at: datetime
    observed_at: datetime
    category: str
    severity: SeverityLevel
    source: str = "pm6_post_trade"
    detector: str
    detector_version: str = "v1"
    description: str
    evidence_refs: tuple[str, ...] = ()
    linked_events: tuple[UUID, ...] = ()
    linked_orders: tuple[UUID, ...] = ()
    scope: str = "account"
    threshold: dict[str, Any] = Field(default_factory=dict)
    observed: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = "review"
    auto_action_status: str = "none"
    truth_source: TruthSource = TruthSource.SIMULATION_TRUTH
    fingerprint: str = ""
    suppressed: bool = False
    suppress_count: int = 0
    correlation_id: UUID | None = None
    trace_id: UUID | None = None

    @field_validator("occurred_at", "created_at", "observed_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value)


class IncidentRecord(ContractModel):
    incident_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    updated_at: datetime
    incident_type: IncidentType
    category: IncidentCategory
    severity: SeverityLevel
    state: IncidentState = IncidentState.DETECTED
    root_cause_hypothesis: str = ""
    linked_alerts: tuple[UUID, ...] = ()
    linked_execution_events: tuple[UUID, ...] = ()
    linked_control_events: tuple[UUID, ...] = ()
    linked_operator_actions: tuple[UUID, ...] = ()
    affected_scope: str = "account"
    owner: str = "pm6"
    containment_status: str = "open"
    remediation_status: str = "open"
    closure_criteria: str = "manual_review"
    review_status: str = "pending"
    truth_source: TruthSource = TruthSource.SIMULATION_TRUTH
    detail: str = ""
    suppressed: bool = False
    suppress_reason: str | None = None

    @field_validator("occurred_at", "updated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value)


class EscalationAction(ContractModel):
    escalation_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    route: EscalationRoute
    target_role: str
    incident_id: UUID
    required_response: str
    deadline_seconds: int = 0
    severity: SeverityLevel
    reason: str
    status: str = "open"
    actor: str = "pm6"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class RemediationTask(ContractModel):
    task_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    incident_id: UUID
    action: str
    owner: str
    priority: SeverityLevel
    due_seconds: int = 0
    closure_criteria: str
    status: str = "open"
    evidence_required: bool = True

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ControlRequest(ContractModel):
    """Typed request toward PM5 control plane. Not a broker command."""

    request_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    kind: ControlRequestKind
    scope: str = "account"
    scope_id: str | None = None
    reason: str
    actor: str = "pm6"
    approval_required: bool = True
    broker_command: bool = False
    status: str = "recommended"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _no_broker(self) -> ControlRequest:
        if self.broker_command:
            raise ValueError("PM6 ControlRequest cannot be a broker command")
        return self


class OrderlyWithdrawalPlan(ContractModel):
    withdrawal_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    scope: str
    trigger_reason: str
    severity: SeverityLevel
    steps: tuple[str, ...] = ()
    pm5_request: ControlRequest | None = None
    close_only: bool = True
    no_new_risk: bool = True
    expected_transitions: tuple[str, ...] = ()
    confirmation_criteria: str = "operator_confirm_plus_recon"
    approval_required: bool = True
    state: WithdrawalState = WithdrawalState.RECOMMENDED
    confirmed: bool = False
    detail: str = ""

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _complete_needs_confirm(self) -> OrderlyWithdrawalPlan:
        if self.state is WithdrawalState.COMPLETED and not self.confirmed:
            raise ValueError("withdrawal cannot complete without confirmation")
        return self


class AuditEvidenceBundle(ContractModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    events: tuple[dict[str, Any], ...] = ()
    control_states: tuple[dict[str, Any], ...] = ()
    incident_ids: tuple[UUID, ...] = ()
    operator_actions: tuple[dict[str, Any], ...] = ()
    timeline: tuple[str, ...] = ()
    provenance: TruthSource = TruthSource.SIMULATION_TRUTH
    policy_version: str = "pm6-seq08-v1"
    fingerprint: str = ""
    persistence_handoff: str = "non_durable_before_pm7"
    durable: bool = False

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class GovernanceReviewPacket(ContractModel):
    packet_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime
    period: str = "session"
    kind: str = "daily"
    incident_trends: dict[str, int] = Field(default_factory=dict)
    alert_trends: dict[str, int] = Field(default_factory=dict)
    unresolved: int = 0
    control_trigger_counts: dict[str, int] = Field(default_factory=dict)
    false_positive_observations: str = "insufficient_data"
    review_flags: tuple[str, ...] = ()
    validation_notes: str = ""
    recommendations: tuple[str, ...] = ()
    state: GovernanceReviewState = GovernanceReviewState.SCHEDULED

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "generated_at")


class ValidationReviewPacket(ContractModel):
    packet_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime
    rule_performance: dict[str, Any] = Field(default_factory=dict)
    alert_precision: str = "insufficient_data"
    false_positive: str = "insufficient_data"
    false_negative: str = "insufficient_data"
    missed_event: str = "insufficient_data"
    control_calibration: str = "not_available"
    data_quality_issues: tuple[str, ...] = ()
    recommended_tuning: tuple[str, ...] = ()
    review_state: GovernanceReviewState = GovernanceReviewState.SCHEDULED
    sample_size: int = 0

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "generated_at")


class MonitoringSnapshot(ContractModel):
    monitoring_id: UUID = Field(default_factory=uuid4)
    as_of: datetime
    state: MonitoringState
    execution_mode: str = "disabled"
    truth_source: TruthSource = TruthSource.UNKNOWN
    active_controls: tuple[str, ...] = ()
    open_orders: int = 0
    fills: int = 0
    positions: int = 0
    exposure: Decimal = Decimal("0")
    alert_count: int = 0
    incident_count: int = 0
    drift_status: str = "none"
    reconciliation_status: str = "degraded"
    broker_truth_available: bool = False
    operational_status: str = "observe_only"
    freshness_seconds: int = 0
    last_event_at: datetime | None = None
    stale: bool = False
    durable: bool = False
    producer: str = "pm6_post_trade"

    @field_validator("as_of", "last_event_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)


class OperationalTruthBundle(ContractModel):
    bundle_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    intake: IntakeRecord
    snapshot: MonitoringSnapshot
    operator_lane: LaneSummary
    control_lane: LaneSummary
    alerts: tuple[PostTradeAlert, ...] = ()
    incidents: tuple[IncidentRecord, ...] = ()
    escalations: tuple[EscalationAction, ...] = ()
    remediation: tuple[RemediationTask, ...] = ()
    withdrawal: OrderlyWithdrawalPlan | None = None
    control_requests: tuple[ControlRequest, ...] = ()
    evidence: AuditEvidenceBundle | None = None
    governance: GovernanceReviewPacket | None = None
    validation: ValidationReviewPacket | None = None
    execution_mode: str = "disabled"
    truth_source: TruthSource = TruthSource.UNKNOWN
    broker_side_effect: bool = False
    mt5_used: bool = False
    durable: bool = False
    producer: str = "pm6_post_trade"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _safety(self) -> OperationalTruthBundle:
        if self.mt5_used:
            raise ValueError("Sequence 08 forbids mt5_used=true")
        if self.broker_side_effect:
            raise ValueError("Sequence 08 forbids broker_side_effect=true")
        if self.truth_source is TruthSource.BROKER_TRUTH:
            raise ValueError("Sequence 08 has no broker truth")
        if self.durable:
            raise ValueError("PM6 evidence is non-durable before PM7")
        return self
