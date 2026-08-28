"""PM3-Strategy Engine supporting contracts (votes, consensus, health).

Not forecasting. Not orders. schema_version remains v1.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.strategy import (
    ConsensusDecision,
    Direction,
    EntryType,
)
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class StrategyTemplateType(str, Enum):
    TREND_PULLBACK = "trend_pullback"
    ORB_SESSION_BREAKOUT = "orb_session_breakout"
    MEAN_REVERSION = "mean_reversion"
    LIQUIDITY_SWEEP_REVERSAL = "liquidity_sweep_reversal"
    VOLATILITY_SQUEEZE_BREAKOUT = "volatility_squeeze_breakout"


class ProfileStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    BACKTEST_CANDIDATE = "backtest_candidate"
    TESTED = "tested"
    PAPER = "paper"
    DEMO_CANDIDATE = "demo_candidate"
    ACTIVE = "active"
    WATCHLIST = "watchlist"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    RETIRED = "retired"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WATCHLIST = "watchlist"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    RETIRED = "retired"
    UNKNOWN = "unknown"


class TuningMode(str, Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"
    RESEARCH = "research"


class ParamType(str, Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    ENUM = "enum"


class VoteAbstentionReason(str, Enum):
    INCOMPATIBLE_REGIME = "incompatible_regime"
    STALE_CONTEXT = "stale_context"
    MALFORMED_CONTEXT = "malformed_context"
    DISABLED_TEMPLATE = "disabled_template"
    DISABLED_PROFILE = "disabled_profile"
    HANDOFF_INELIGIBLE = "handoff_ineligible"
    SYSTEM_FLAG = "system_flag"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DATA_QUALITY = "data_quality"
    LOOKAHEAD = "lookahead"
    FEATURE_FLAG_OFF = "feature_flag_off"
    MAX_BRANCHES = "max_branches"
    DUPLICATE_INTENT = "duplicate_intent"
    CONSENSUS_WAIT = "consensus_wait"
    CONSENSUS_NO_TRADE = "consensus_no_trade"
    NONE = "none"


class StrategyEventType(str, Enum):
    VOTE = "vote"
    CONSENSUS = "consensus"
    INTENT = "intent"
    NO_TRADE = "no_trade"
    PROFILE_CHANGE = "profile_change"
    HEALTH = "health"
    FEEDBACK = "feedback"


class ProfileChangeAction(str, Enum):
    CLONE_DRAFT = "clone_draft"
    UPDATE_DRAFT = "update_draft"
    APPLY_PRESET = "apply_preset"
    VALIDATE = "validate"
    PROMOTE = "promote"
    ACTIVATE = "activate"
    REPLACE_BINDING = "replace_binding"
    ROLLBACK = "rollback"
    DISABLE = "disable"


class StrategyVote(ContractModel):
    vote_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    occurred_at: datetime
    strategy_template_type: StrategyTemplateType
    profile_id: str
    version_id: str
    symbol: str
    direction: Direction = Direction.FLAT
    raw_probability: float = Field(ge=0.0, le=1.0)
    calibrated_probability: float = Field(ge=0.0, le=1.0)
    setup_quality: float = Field(ge=0.0, le=1.0)
    regime_fit: float = Field(ge=0.0, le=1.0)
    friction_fit: float = Field(ge=0.0, le=1.0)
    historical_reliability: float = Field(ge=0.0, le=1.0)
    recent_live_health: float = Field(ge=0.0, le=1.0)
    entry_type: EntryType = EntryType.LIMIT
    entry_hints: dict[str, Any] = Field(default_factory=dict)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    abstained: bool = False
    abstention_reason: VoteAbstentionReason = VoteAbstentionReason.NONE
    calibration_version: str = "reliability_table.v1"
    calibration_fallback: bool = False
    producer: str = "pm3_strategy_engine"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class SymbolConsensusResult(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    symbol: str
    decision: ConsensusDecision
    p_long: float = Field(ge=0.0, le=1.0)
    p_short: float = Field(ge=0.0, le=1.0)
    agreement_score: float = Field(ge=0.0, le=1.0)
    conflict_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    selected_votes: tuple[UUID, ...] = ()
    dropped_votes: tuple[UUID, ...] = ()
    abstention_reason: VoteAbstentionReason | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    producer: str = "pm3_strategy_engine"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class ProfileHealthSnapshot(ContractModel):
    profile_id: str
    version_id: str
    as_of: datetime
    health_status: HealthStatus = HealthStatus.UNKNOWN
    degradation_triggers: tuple[str, ...] = ()
    alerts: tuple[str, ...] = ()
    recommended_action: str = "observe"
    last_updated_at: datetime | None = None

    @field_validator("as_of", "last_updated_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)


class TrackerSnapshot(ContractModel):
    profile_id: str
    version_id: str
    as_of: datetime
    signals_today: int = 0
    intents_today: int = 0
    trades_today: int | None = None
    realized_r: float | None = None
    average_spread: float | None = None
    average_slippage: float | None = None
    current_state: str = "observe-only"
    win_rate: float | None = None
    expectancy_r: float | None = None
    profit_factor: float | None = None
    mae: float | None = None
    mfe: float | None = None
    max_drawdown_r: float | None = None
    hold_time_distribution: dict[str, Any] | None = None
    exit_reason_distribution: dict[str, Any] | None = None
    out_of_sample_delta: float | None = None
    live_vs_backtest_drift: float | None = None
    insufficient_data: bool = True

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class StrategyDiagnostics(ContractModel):
    as_of: datetime
    symbol: str | None = None
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class ValidationReport(ContractModel):
    ok: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    fingerprint: str | None = None


class ConfigChangePreview(ContractModel):
    action: ProfileChangeAction
    profile_id: str
    version_id: str | None = None
    diff: dict[str, Any] = Field(default_factory=dict)
    requires_revalidation: bool = True


class StrategyFeedbackEvent(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    occurred_at: datetime
    symbol: str
    intent_id: UUID | None = None
    profile_id: str
    version_id: str
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    valid: bool = True

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
