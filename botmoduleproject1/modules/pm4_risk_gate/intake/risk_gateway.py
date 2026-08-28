"""Normalize upstream artifacts into a canonical PM4 intake object."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.pm2 import RankedCandidate
from botmoduleproject1.contracts.v1.risk import ExposureSnapshot
from botmoduleproject1.contracts.v1.strategy import TradeIntent
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.modules.pm4_risk_gate.domain.ids import new_id
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


class RiskIntakeGateway:
    def normalize(
        self,
        intent: TradeIntent,
        exposure: ExposureSnapshot,
        *,
        candidate: RankedCandidate | None = None,
        forecast: ForecastOutput | None = None,
        as_of: datetime | None = None,
        mid_price=None,
        spread=None,
        session: str | None = None,
        trace: dict[str, Any] | None = None,
    ) -> RiskIntakeRequest:
        stamp = ensure_aware_utc(as_of or intent.occurred_at, "as_of")
        return RiskIntakeRequest(
            workflow_id=new_id(),
            as_of=stamp,
            intent=intent,
            candidate=candidate,
            forecast=forecast,
            exposure=exposure,
            mid_price=mid_price,
            spread=spread,
            session=session,
            trace=dict(trace or {}),
        )
