"""Canonical PM4 intake object. Not an order."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.pm2 import RankedCandidate
from botmoduleproject1.contracts.v1.risk import ExposureSnapshot
from botmoduleproject1.contracts.v1.strategy import TradeIntent


class RiskIntakeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: UUID = Field(default_factory=uuid4)
    as_of: datetime
    intent: TradeIntent
    candidate: RankedCandidate | None = None
    forecast: ForecastOutput | None = None
    exposure: ExposureSnapshot
    mid_price: Decimal | None = None
    spread: Decimal | None = None
    session: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)
