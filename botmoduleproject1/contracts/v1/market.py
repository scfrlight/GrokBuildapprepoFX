"""Market data contracts (PM2 inbound)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class Timeframe(str, Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"


class SymbolMetadata(ContractModel):
    symbol: str = Field(min_length=3, max_length=32)
    base_currency: str = Field(min_length=3, max_length=8)
    quote_currency: str = Field(min_length=3, max_length=8)
    digits: int = Field(ge=0, le=8)
    point: Decimal
    contract_size: Decimal
    broker_symbol: str | None = None


class OhlcvBar(ContractModel):
    symbol: str
    timeframe: Timeframe
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")
    broker_as_of: datetime | None = None

    @field_validator("open_time", "broker_as_of")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)


class Tick(ContractModel):
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp: datetime
    stale: bool = False

    @field_validator("timestamp")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "timestamp")
