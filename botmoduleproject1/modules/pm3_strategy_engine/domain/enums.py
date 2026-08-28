"""Re-export canonical enumerations. Do not fork Direction/RegimeType."""

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import (
    ConsensusDecision,
    Direction,
    EntryType,
    StopType,
    UrgencyClass,
)
from botmoduleproject1.contracts.v1.strategy_engine import (
    HealthStatus,
    ParamType,
    ProfileChangeAction,
    ProfileStatus,
    StrategyEventType,
    StrategyTemplateType,
    TuningMode,
    VoteAbstentionReason,
)

FIRST_PHASE = (
    StrategyTemplateType.TREND_PULLBACK,
    StrategyTemplateType.ORB_SESSION_BREAKOUT,
    StrategyTemplateType.MEAN_REVERSION,
)
SECOND_PHASE = (
    StrategyTemplateType.LIQUIDITY_SWEEP_REVERSAL,
    StrategyTemplateType.VOLATILITY_SQUEEZE_BREAKOUT,
)

ACTIVATABLE = {
    ProfileStatus.VALIDATED,
    ProfileStatus.TESTED,
    ProfileStatus.DEMO_CANDIDATE,
}
NON_VOTING = {
    ProfileStatus.DRAFT,
    ProfileStatus.DISABLED,
    ProfileStatus.DEGRADED,
    ProfileStatus.RETIRED,
}

__all__ = [
    "ACTIVATABLE",
    "ConsensusDecision",
    "Direction",
    "EntryType",
    "FIRST_PHASE",
    "HealthStatus",
    "NON_VOTING",
    "ParamType",
    "ProfileChangeAction",
    "ProfileStatus",
    "RegimeType",
    "SECOND_PHASE",
    "StopType",
    "StrategyEventType",
    "StrategyTemplateType",
    "TuningMode",
    "UrgencyClass",
    "VoteAbstentionReason",
]
