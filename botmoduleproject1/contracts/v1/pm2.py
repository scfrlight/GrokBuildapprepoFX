"""PM2 public output contracts. Ranked intelligence — not orders.

Consumed later by PM3-Strategy Engine (context/snapshot) and PM3 forecasting
(enrichment only). Never carries broker actions or position sizes.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.session import RegimeType, SessionName
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class QualityTier(str, Enum):
    SUPPRESS = "suppress"
    WATCH = "watch"
    ELIGIBLE = "eligible"
    HIGH = "high"
    TOP = "top"


class QualificationStateName(str, Enum):
    NEUTRAL = "neutral"
    FORMING = "forming"
    QUALIFIED = "qualified"
    CONFIRMED = "confirmed"
    COOLDOWN = "cooldown"
    SUPPRESSED = "suppressed"
    INVALIDATED = "invalidated"
    STALE = "stale"


class DataQualityStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    STALE = "stale"
    INCOMPLETE = "incomplete"
    MALFORMED = "malformed"


class FeatureFamily(str, Enum):
    REGIME = "regime"
    DIRECTIONAL_BIAS = "directional_bias"
    STRUCTURE = "structure"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    SESSION_LIQUIDITY = "session_liquidity"
    CORRELATION = "correlation"
    MACRO = "macro"


class CandidateContextSnapshot(ContractModel):
    candidate_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    symbol: str
    as_of: datetime
    timeframes: tuple[str, ...] = ()
    regime: RegimeType
    regime_confidence: float = Field(ge=0.0, le=1.0)
    sessions: tuple[SessionName, ...] = ()
    session_quality: float = Field(default=0.5, ge=0.0, le=1.0)
    data_quality: DataQualityStatus
    feature_family_summary: dict[str, float] = Field(default_factory=dict)
    feature_set_version: str = "pm2.features.v1"
    producer: str = "pm2_market_context"

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class CandidateScoreCard(ContractModel):
    long_score: float = Field(ge=0.0, le=100.0)
    short_score: float = Field(ge=0.0, le=100.0)
    final_confluence_score: float = Field(ge=0.0, le=100.0)
    directional_edge_gap: float = Field(ge=0.0, le=100.0)
    regime_score: float = Field(ge=0.0, le=100.0)
    structure_score: float = Field(ge=0.0, le=100.0)
    momentum_score: float = Field(ge=0.0, le=100.0)
    volatility_score: float = Field(ge=0.0, le=100.0)
    session_score: float = Field(ge=0.0, le=100.0)
    liquidity_score: float = Field(ge=0.0, le=100.0)
    correlation_penalty: float = Field(ge=0.0, le=100.0)
    feature_redundancy_penalty: float = Field(ge=0.0, le=100.0)
    confidence_score: float = Field(ge=0.0, le=100.0)
    quality_tier: QualityTier
    components: dict[str, float] = Field(default_factory=dict)
    vetoes: tuple[str, ...] = ()


class CandidateQualificationState(ContractModel):
    state: QualificationStateName
    entered_at: datetime
    persistence_count: int = Field(ge=0, default=0)
    cooldown_until: datetime | None = None
    stale_after: datetime | None = None
    last_transition_reason: str = ""

    @field_validator("entered_at", "cooldown_until", "stale_after")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)


class SuppressionRecord(ContractModel):
    symbol: str
    as_of: datetime
    suppression_reasons: tuple[str, ...]
    veto_triggers: tuple[str, ...] = ()
    conflict_group: str | None = None
    ghost_tracking_eligibility: bool = True

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class RankedCandidate(ContractModel):
    candidate_id: UUID
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    symbol: str
    as_of: datetime
    final_rank: int = Field(ge=1)
    shortlist_rank: int | None = None
    scorecard: CandidateScoreCard
    state: CandidateQualificationState
    context: CandidateContextSnapshot
    suppression: SuppressionRecord | None = None
    correlation_cluster: str | None = None
    handoff_eligibility: bool = False
    side_bias: str = "flat"
    timing_valid_until: datetime | None = None
    producer: str = "pm2_market_context"

    @field_validator("as_of", "timing_valid_until")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)


class PublicationBundle(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    as_of: datetime
    shortlist: tuple[RankedCandidate, ...] = ()
    watchlist: tuple[RankedCandidate, ...] = ()
    suppressed: tuple[SuppressionRecord, ...] = ()
    diagnostics_summary: dict[str, Any] = Field(default_factory=dict)
    health_summary: dict[str, Any] = Field(default_factory=dict)
    calibration_snapshot: dict[str, Any] = Field(default_factory=dict)
    feature_set_version: str = "pm2.features.v1"
    producer: str = "pm2_market_context"
    idempotency_key: str | None = None

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


def quality_tier_for(score: float) -> QualityTier:
    if score < 40:
        return QualityTier.SUPPRESS
    if score < 60:
        return QualityTier.WATCH
    if score < 75:
        return QualityTier.ELIGIBLE
    if score < 90:
        return QualityTier.HIGH
    return QualityTier.TOP
