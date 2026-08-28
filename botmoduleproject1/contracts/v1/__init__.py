"""Contract-first domain schemas, version v1.

PM3-Strategy Engine types live in ``strategy``.
PM3 forecasting / QRF types live in ``forecasting``.
Those namespaces must never be merged.
"""

from botmoduleproject1.contracts.v1.alerts import (
    AlertEvent,
    AlertSeverity,
    ApprovalRequest,
    ApprovalStatus,
)
from botmoduleproject1.contracts.v1.execution import (
    ExecutionReport,
    OrderRequest,
    OrderStatus,
    Position,
    ReconciliationRecord,
)
from botmoduleproject1.contracts.v1.forecasting import (
    ForecastOutput,
    ModelVersionInfo,
    QuantileSet,
)
from botmoduleproject1.contracts.v1.identity import SCHEMA_VERSION, EventEnvelope
from botmoduleproject1.contracts.v1.journal import EventType, JournalEntry
from botmoduleproject1.contracts.v1.market import OhlcvBar, SymbolMetadata, Tick, Timeframe
from botmoduleproject1.contracts.v1.pm2 import (
    CandidateContextSnapshot,
    CandidateQualificationState,
    CandidateScoreCard,
    DataQualityStatus,
    FeatureFamily,
    PublicationBundle,
    QualificationStateName,
    QualityTier,
    RankedCandidate,
    SuppressionRecord,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.risk import (
    ExposureSnapshot,
    RiskRejectionReason,
    RiskVerdict,
    RiskVerdictStatus,
)
from botmoduleproject1.contracts.v1.roles import OperatorRole, PermissionScope
from botmoduleproject1.contracts.v1.session import (
    RegimeState,
    RegimeType,
    SessionContext,
    SessionName,
)
from botmoduleproject1.contracts.v1.signals import ConfluenceScore, SignalEvent
from botmoduleproject1.contracts.v1.strategy import (
    ConsensusDecision,
    Direction,
    EntryType,
    ExitPlan,
    NoTradeDecision,
    StopType,
    TradeIntent,
    UrgencyClass,
)
from botmoduleproject1.contracts.v1.strategy_engine import (
    ConfigChangePreview,
    HealthStatus,
    ProfileChangeAction,
    ProfileHealthSnapshot,
    ProfileStatus,
    StrategyDiagnostics,
    StrategyFeedbackEvent,
    StrategyTemplateType,
    StrategyVote,
    SymbolConsensusResult,
    TrackerSnapshot,
    ValidationReport,
    VoteAbstentionReason,
)
from botmoduleproject1.contracts.v1.time import UTC, ensure_aware_utc, utc_now
from botmoduleproject1.contracts.v1.tuning import (
    ParameterSchema,
    TuningChangeRequest,
    TuningChangeStatus,
)

__all__ = [
    "SCHEMA_VERSION",
    "UTC",
    "AlertEvent",
    "AlertSeverity",
    "ApprovalRequest",
    "ApprovalStatus",
    "CandidateContextSnapshot",
    "CandidateQualificationState",
    "CandidateScoreCard",
    "ConfluenceScore",
    "ConfigChangePreview",
    "ConsensusDecision",
    "DataQualityStatus",
    "Direction",
    "EventEnvelope",
    "EventType",
    "ExecutionReport",
    "ExitPlan",
    "ExposureSnapshot",
    "FeatureFamily",
    "ForecastOutput",
    "HealthStatus",
    "JournalEntry",
    "ModelVersionInfo",
    "NoTradeDecision",
    "OhlcvBar",
    "OperatorRole",
    "OrderRequest",
    "OrderStatus",
    "ParameterSchema",
    "PermissionScope",
    "Position",
    "ProfileChangeAction",
    "ProfileHealthSnapshot",
    "ProfileStatus",
    "PublicationBundle",
    "QualificationStateName",
    "QualityTier",
    "QuantileSet",
    "RankedCandidate",
    "ReconciliationRecord",
    "RegimeState",
    "RegimeType",
    "RiskRejectionReason",
    "RiskVerdict",
    "RiskVerdictStatus",
    "SessionContext",
    "SessionName",
    "SignalEvent",
    "StopType",
    "StrategyDiagnostics",
    "StrategyFeedbackEvent",
    "StrategyTemplateType",
    "StrategyVote",
    "SuppressionRecord",
    "SymbolConsensusResult",
    "SymbolMetadata",
    "Tick",
    "Timeframe",
    "TrackerSnapshot",
    "TradeIntent",
    "TuningChangeRequest",
    "TuningChangeStatus",
    "UrgencyClass",
    "ValidationReport",
    "VoteAbstentionReason",
    "ensure_aware_utc",
    "quality_tier_for",
    "utc_now",
    "EntryType",
]
