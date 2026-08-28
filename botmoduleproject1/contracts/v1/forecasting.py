"""PM3 forecasting / QRF contracts.

Separate from the PM3-Strategy Engine. Forecasts enrich uncertainty;
they never create or mutate trade side.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class QuantileSet(ContractModel):
    """Price-space quantile envelope. Non-decreasing. Not a direction vote."""

    q05: Decimal
    q25: Decimal
    q50: Decimal
    q75: Decimal
    q95: Decimal

    @model_validator(mode="after")
    def _non_decreasing(self) -> QuantileSet:
        ordered = (self.q05, self.q25, self.q50, self.q75, self.q95)
        if any(ordered[i] > ordered[i + 1] for i in range(len(ordered) - 1)):
            raise ValueError(
                "quantiles must be non-decreasing: q05 <= q25 <= q50 <= q75 <= q95"
            )
        return self


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
    coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    sample_size: int | None = Field(default=None, ge=0)
    horizon_seconds: int | None = Field(default=None, ge=1)
    diagnostics: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")
