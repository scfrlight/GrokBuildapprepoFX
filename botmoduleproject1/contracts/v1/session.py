"""Session and regime contracts (PM2)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class SessionName(str, Enum):
    SYDNEY = "sydney"
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP_LONDON_NY = "overlap_london_ny"
    OFF_SESSION = "off_session"
    ROLLOVER = "rollover"


class SessionContext(ContractModel):
    as_of: datetime
    sessions: tuple[SessionName, ...] = ()
    is_weekend: bool = False
    is_holiday: bool = False
    quality: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class RegimeType(str, Enum):
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    COMPRESSION = "compression"
    TRANSITIONAL = "transitional"
    UNTRADEABLE = "untradeable"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class RegimeState(ContractModel):
    symbol: str
    regime: RegimeType
    confidence: float = Field(ge=0.0, le=1.0)
    as_of: datetime
    method: str = "unspecified"
    persistence_bars: int = 0

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")
