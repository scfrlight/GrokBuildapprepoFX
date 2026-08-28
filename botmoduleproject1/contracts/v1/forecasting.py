"""PM3 forecasting / QRF contracts.

Separate from the PM3-Strategy Engine. Forecasts enrich uncertainty;
they never create or mutate trade side.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class QuantileSet(ContractModel):
    q05: Decimal
    q25: Decimal
    q50: Decimal
    q75: Decimal
    q95: Decimal


class ModelVersionInfo(ContractModel):
    model_id: str
    version: str
    trained_at: datetime | None = None
    registry_uri: str | None = None

    @field_validator("trained_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value, "trained_at")


class ForecastOutput(ContractModel):
    """Uncertainty envelope attached to an intent. Not an order."""

    forecast_id: UUID
    intent_id: UUID
    event_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    occurred_at: datetime
    symbol: str
    horizon_bars: int = Field(ge=1)
    quantiles: QuantileSet
    model: ModelVersionInfo
    producer: str = "pm3_forecasting"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
