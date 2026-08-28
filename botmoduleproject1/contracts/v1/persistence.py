"""PM7 persistence, journal, evidence, replay, and audit contracts.

Sequence 09. These types do not replace PM4 risk, PM5 execution, or PM6
post-trade contracts. PM7 never creates orders. Simulation truth is never
broker truth. Committed journal entries are immutable.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class PersistenceMode(str, Enum):
    DISABLED = "disabled"
    MEMORY = "memory"
    FILE_BACKED = "file_backed"
    SQLITE_LOCAL = "sqlite_local"
    DURABLE_CANDIDATE = "durable_candidate"
    PRODUCTION_DURABLE = "production_durable"


class PersistenceTruthSource(str, Enum):
    PM2_CONTEXT = "pm2_context"
    PM3_STRATEGY = "pm3_strategy"
    PM3_FORECAST = "pm3_forecast"
    PM4_RISK = "pm4_risk"
    PM5_LOCAL_OMS = "pm5_local_oms"
    PM5_SIMULATION = "pm5_simulation"
    PM5_BROKER = "pm5_broker"
    PM6_MONITORING = "pm6_monitoring"
    OPERATOR = "operator"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class IngestDisposition(str, Enum):
    ACCEPTED = "accepted"
    COMMITTED = "committed"
    DUPLICATE_IGNORED = "duplicate_ignored"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    CONTRADICTION_RECORDED = "contradiction_recorded"
    DEGRADED = "degraded"
    FEATURE_DISABLED = "feature_disabled"


class JournalCategory(str, Enum):
    SIGNAL_REFERENCE = "signal_reference"
    STRATEGY_DECISION = "strategy_decision"
    FORECAST = "forecast"
    RISK_DECISION = "risk_decision"
    SIZING = "sizing"
    HEAT_CONTROL = "heat_control"
    ORDER_INTENT = "order_intent"
    ORDER_LIFECYCLE = "order_lifecycle"
    BROKER_ACKNOWLEDGEMENT = "broker_acknowledgement"
    FILL = "fill"
    POSITION = "position"
    RECONCILIATION = "reconciliation"
    SURVEILLANCE = "surveillance"
    INCIDENT = "incident"
    ESCALATION = "escalation"
    REMEDIATION = "remediation"
    WITHDRAWAL = "withdrawal"
    OPERATOR_ACTION = "operator_action"
    PARAMETER_CHANGE = "parameter_change"
    CONFIGURATION_CHANGE = "configuration_change"
    SNAPSHOT = "snapshot"
    REPLAY = "replay"
    INTEGRITY = "integrity"
    RETENTION_ARCHIVE = "retention_archive"
    RECOVERY = "recovery"
    CORRECTION = "correction"


class ReconciliationPersistState(str, Enum):
    PASS = "pass"
    MISMATCH = "mismatch"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    CRITICAL = "critical"
    RESOLVED = "resolved"
    REQUIRES_REVIEW = "requires_review"


class EvidenceState(str, Enum):
    DRAFT = "draft"
    ASSEMBLED = "assembled"
    VERIFIED = "verified"
    EXPORTED = "exported"
    ARCHIVED = "archived"
    FROZEN = "frozen"


class ReplayState(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    DIVERGENCE_DETECTED = "divergence_detected"
    FAILED = "failed"
    VERIFIED = "verified"


class ReplayScope(str, Enum):
    SESSION = "session"
    INCIDENT = "incident"
    ORDER = "order"
    SYMBOL = "symbol"
    STRATEGY = "strategy"
    CONTROL = "control"
    RECONCILIATION = "reconciliation"


class SnapshotScope(str, Enum):
    SYSTEM = "system"
    SESSION = "session"
    SYMBOL = "symbol"
    ORDER = "order"
    POSITION = "position"
    PM4_CONTROL = "pm4_control"
    PM5_CONTROL = "pm5_control"
    PM6_MONITORING = "pm6_monitoring"
    INCIDENT = "incident"


class SnapshotState(str, Enum):
    PENDING = "pending"
    CAPTURED = "captured"
    VALIDATED = "validated"
    STALE = "stale"
    SUPERSEDED = "superseded"
    CORRUPT = "corrupt"


class IntegrityState(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    WARNING = "warning"
    COMPROMISED = "compromised"
    REPAIRED = "repaired"


class ArchiveTier(str, Enum):
    ACTIVE = "active"
    WARM = "warm"
    COLD = "cold"
    FROZEN = "frozen"
    RETENTION_LOCK = "retention_lock"
    EXPIRED = "expired"
    PURGE_ELIGIBLE = "purge_eligible"
    PURGED_IF_ALLOWED = "purged_if_allowed"


class RecoveryStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    STALE = "stale"
    VERIFICATION_FAILED = "verification_failed"
    RESTORE_PENDING = "restore_pending"
    RESTORED = "restored"
    REQUIRES_REVIEW = "requires_review"


class ReportKind(str, Enum):
    DAILY_OPERATIONS = "daily_operations"
    INCIDENT_REVIEW = "incident_review"
    RECONCILIATION_HEALTH = "reconciliation_health"
    CONTROL_ACTIVITY = "control_activity"
    AUDIT_EVIDENCE_INDEX = "audit_evidence_index"
    DATA_QUALITY = "data_quality"
    INTEGRITY_VERIFICATION = "integrity_verification"
    GOVERNANCE_REVIEW = "governance_review"


class DataQualityStatus(str, Enum):
    OK = "ok"
    INSUFFICIENT_DATA = "insufficient_data"
    NOT_AVAILABLE = "not_available"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


_SECRET_KEYS = frozenset({"password", "token", "secret", "dsn", "credential", "api_key"})


def _strip_secrets(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if any(token in lowered for token in _SECRET_KEYS):
            continue
        if isinstance(value, dict):
            out[key] = _strip_secrets(value)
        else:
            out[key] = value
    return out


class LedgerEvent(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    session_id: str | None = None
    source_module: str
    source_entity_id: str | None = None
    event_type: str
    event_version: str = "v1"
    event_timestamp: datetime
    ingested_at: datetime | None = None
    source_timestamp: datetime | None = None
    event_payload: dict[str, Any] = Field(default_factory=dict)
    truth_source: PersistenceTruthSource = PersistenceTruthSource.UNKNOWN
    lineage_refs: tuple[str, ...] = ()
    integrity_metadata: dict[str, Any] = Field(default_factory=dict)
    operator_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    category: JournalCategory = JournalCategory.ORDER_LIFECYCLE
    ticket: str | None = None
    symbol: str | None = None
    order_id: str | None = None
    strategy_id: str | None = None
    incident_id: str | None = None

    @field_validator("event_timestamp", "ingested_at", "source_timestamp")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return ensure_aware_utc(value, "timestamp")

    @field_validator("source_module", "event_type")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped

    @model_validator(mode="after")
    def _provenance(self) -> LedgerEvent:
        ticket = self.ticket or ""
        if ticket.startswith("SIM-") and self.truth_source is PersistenceTruthSource.PM5_BROKER:
            raise ValueError("SIM-* cannot be mapped to pm5_broker")
        payload = self.event_payload
        if payload.get("mt5_used") is True:
            raise ValueError("PM7 forbids mt5_used=true")
        if payload.get("broker_side_effect") is True:
            raise ValueError("PM7 forbids broker_side_effect=true")
        object.__setattr__(self, "event_payload", _strip_secrets(dict(payload)))
        return self


class CommittedJournalRecord(ContractModel):
    sequence: int = Field(ge=1)
    event: LedgerEvent
    content_hash: str
    previous_hash: str
    committed_at: datetime
    disposition: IngestDisposition = IngestDisposition.COMMITTED

    @field_validator("committed_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "committed_at")


class IngestResult(ContractModel):
    disposition: IngestDisposition
    event_id: UUID | None = None
    sequence: int | None = None
    content_hash: str | None = None
    reasons: tuple[str, ...] = ()
    truth_source: PersistenceTruthSource = PersistenceTruthSource.UNKNOWN
    durable: bool = False


class ReconciliationPersistRecord(ContractModel):
    record_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    order_id: str | None = None
    session_id: str | None = None
    symbol: str | None = None
    state: ReconciliationPersistState
    broker_truth_available: bool = False
    truth_source: PersistenceTruthSource = PersistenceTruthSource.PM5_SIMULATION
    source_event_id: UUID | None = None
    notes: str = ""
    local_state: dict[str, Any] = Field(default_factory=dict)
    broker_state: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _no_silent_pass(self) -> ReconciliationPersistRecord:
        if (
            not self.broker_truth_available
            and self.state is ReconciliationPersistState.PASS
        ):
            raise ValueError("reconciliation without venue cannot be pass")
        return self


class EvidenceBundle(ContractModel):
    bundle_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    state: EvidenceState = EvidenceState.ASSEMBLED
    what: str
    when: datetime
    module: str
    entity_id: str | None = None
    changed: str = ""
    why: str = ""
    actor: str | None = None
    result: str = ""
    unresolved: tuple[str, ...] = ()
    truth_source: PersistenceTruthSource
    integrity_status: IntegrityState = IntegrityState.UNKNOWN
    source_event_ids: tuple[str, ...] = ()
    snapshot_ids: tuple[str, ...] = ()
    timeline: tuple[str, ...] = ()
    lineage_refs: tuple[str, ...] = ()
    policy_version: str = "v1"
    summary: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    durable: bool = False

    @field_validator("occurred_at", "when")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "timestamp")


class ReplayResult(ContractModel):
    replay_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    scope: ReplayScope
    state: ReplayState
    event_count: int = 0
    timeline: tuple[str, ...] = ()
    reconstructed: dict[str, Any] = Field(default_factory=dict)
    snapshot_comparison: dict[str, Any] = Field(default_factory=dict)
    divergence_notes: tuple[str, ...] = ()
    verification: IntegrityState = IntegrityState.UNKNOWN
    source_lineage: tuple[str, ...] = ()

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class SnapshotRecord(ContractModel):
    snapshot_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    scope: SnapshotScope
    state: SnapshotState = SnapshotState.CAPTURED
    journal_sequence: int = Field(ge=0)
    schema_version: str = "v1"
    checksum: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class IntegrityReport(ContractModel):
    report_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    state: IntegrityState
    records_checked: int = 0
    chain_valid: bool = False
    mismatch_details: tuple[str, ...] = ()
    genesis_hash: str = ""
    tip_hash: str | None = None
    claim: str = "tamper_detection_only"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class RetentionStatus(ContractModel):
    occurred_at: datetime
    tier: ArchiveTier = ArchiveTier.ACTIVE
    frozen: bool = False
    lock_reason: str | None = None
    purge_eligible: bool = False
    simulated: bool = True
    manifest_checksum: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class QuerySpec(ContractModel):
    query_id: UUID = Field(default_factory=uuid4)
    actor: str
    authorized: bool = False
    trace_id: str | None = None
    session_id: str | None = None
    symbol: str | None = None
    strategy_id: str | None = None
    order_id: str | None = None
    decision_id: str | None = None
    incident_id: str | None = None
    category: JournalCategory | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class QueryResult(ContractModel):
    query_id: UUID
    authorized: bool
    parameters: dict[str, Any] = Field(default_factory=dict)
    event_ids: tuple[str, ...] = ()
    count: int = 0
    offset: int = 0
    limit: int = 50
    provenance: tuple[str, ...] = ()
    access: str = "rejected"
    reasons: tuple[str, ...] = ()


class ExportPackage(ContractModel):
    package_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    kind: str
    json_payload: dict[str, Any] = Field(default_factory=dict)
    markdown: str = ""
    manifest: dict[str, Any] = Field(default_factory=dict)
    checksum: str
    lineage_refs: tuple[str, ...] = ()
    integrity_status: IntegrityState = IntegrityState.UNKNOWN
    truth_source: PersistenceTruthSource = PersistenceTruthSource.UNKNOWN

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _no_secrets(self) -> ExportPackage:
        object.__setattr__(self, "json_payload", _strip_secrets(dict(self.json_payload)))
        object.__setattr__(self, "manifest", _strip_secrets(dict(self.manifest)))
        return self


class AnalyticsDataset(ContractModel):
    dataset_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    scope: str
    transformation_version: str = "v1"
    source_event_ids: tuple[str, ...] = ()
    metrics: dict[str, Any] = Field(default_factory=dict)
    metric_definitions: dict[str, str] = Field(default_factory=dict)
    quality: DataQualityStatus = DataQualityStatus.INSUFFICIENT_DATA
    truth_source: PersistenceTruthSource = PersistenceTruthSource.DERIVED

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class AuditReport(ContractModel):
    report_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    kind: ReportKind
    summary: str
    dataset: AnalyticsDataset
    lineage_refs: tuple[str, ...] = ()
    quality: DataQualityStatus = DataQualityStatus.INSUFFICIENT_DATA

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class BackupMetadata(ContractModel):
    backup_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    status: RecoveryStatus
    reference: str | None = None
    journal_sequence: int = 0
    checksum: str | None = None
    notes: str = "metadata_only_no_external_backup_service"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class PersistencePublicationBundle(ContractModel):
    bundle_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    mode: PersistenceMode
    journal_sequence: int = 0
    ingest: IngestResult | None = None
    integrity: IntegrityState = IntegrityState.UNKNOWN
    retention: ArchiveTier = ArchiveTier.ACTIVE
    reconciliation_state: ReconciliationPersistState | None = None
    evidence_id: UUID | None = None
    replay_id: UUID | None = None
    truth_source: PersistenceTruthSource = PersistenceTruthSource.UNKNOWN
    persistence_handoff: str = "pending_pm8"
    broker_side_effect: bool = False
    mt5_used: bool = False
    durable: bool = False
    producer: str = "pm7_persistence"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _safety(self) -> PersistencePublicationBundle:
        if self.mt5_used:
            raise ValueError("PM7 forbids mt5_used=true")
        if self.broker_side_effect:
            raise ValueError("PM7 forbids broker_side_effect=true")
        if self.mode is PersistenceMode.PRODUCTION_DURABLE:
            raise ValueError("production_durable is refused in Sequence 09")
        if self.durable and self.mode is PersistenceMode.MEMORY:
            raise ValueError("memory mode cannot claim durable=true")
        return self
