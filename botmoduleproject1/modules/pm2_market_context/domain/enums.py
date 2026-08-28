"""PM2 domain enumerations. Pair-agnostic."""

from __future__ import annotations

from enum import Enum

from botmoduleproject1.contracts.v1.pm2 import (
    DataQualityStatus,
    FeatureFamily,
    QualificationStateName,
    QualityTier,
)
from botmoduleproject1.contracts.v1.session import RegimeType, SessionName


class VolatilityPhase(str, Enum):
    COMPRESSION = "compression"
    EXPANSION = "expansion"
    EXHAUSTION = "exhaustion"
    SHOCK = "shock"
    DEAD = "dead"


class OperatingMode(str, Enum):
    SHADOW = "shadow"
    PAPER = "paper"
    ACTIVE_INTELLIGENCE = "active-intelligence"


class RankingMode(str, Enum):
    DETERMINISTIC = "deterministic"
    LTR_READY = "ltr-ready"


class StructureState(str, Enum):
    CONTINUATION = "continuation"
    BREAK = "break"
    TRANSITION = "transition"
    INVALIDATION = "invalidation"
    UNDEFINED = "undefined"


__all__ = [
    "DataQualityStatus",
    "FeatureFamily",
    "OperatingMode",
    "QualificationStateName",
    "QualityTier",
    "RankingMode",
    "RegimeType",
    "SessionName",
    "StructureState",
    "VolatilityPhase",
]
