"""Value objects for evaluation. Not PM2 internals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, RankedCandidate
from botmoduleproject1.contracts.v1.session import RegimeType


@dataclass(frozen=True)
class SystemFlags:
    strategy_evaluation_enabled: bool = True
    observe_only: bool = True
    live_trading: bool = False


@dataclass(frozen=True)
class PortfolioContext:
    """Placeholder. Not a risk decision."""

    as_of: datetime
    note: str = "placeholder; PM4 not implemented"


@dataclass(frozen=True)
class RiskContext:
    """Placeholder. Presence is not ALLOW."""

    as_of: datetime
    approved: bool = False
    note: str = "placeholder; only PM4 may ALLOW"


@dataclass(frozen=True)
class ExecutionContext:
    """Placeholder. Not a broker session."""

    as_of: datetime
    connected: bool = False


@dataclass(frozen=True)
class SymbolState:
    symbol: str
    as_of: datetime
    last_intent_key: str | None = None
    last_decision: str | None = None


@dataclass(frozen=True)
class FeatureView:
    """Strategy-side feature view adapted from public PM2 snapshot/scorecard."""

    family_summary: dict[str, float] = field(default_factory=dict)
    confluence: float = 0.0
    long_score: float = 0.0
    short_score: float = 0.0
    structure: float = 0.0
    momentum: float = 0.0
    volatility: float = 0.0
    session: float = 0.0


@dataclass(frozen=True)
class EvaluationContext:
    symbol: str
    as_of: datetime
    candidate_id: UUID
    candidate: RankedCandidate
    regime: RegimeType
    data_quality: DataQualityStatus
    stale: bool
    malformed: bool
    lookahead: bool
    handoff_eligible: bool
    session_quality: float
    side_bias: str
    features: FeatureView
    params: dict[str, Any]
    profile_id: str
    version_id: str
    flags: SystemFlags
