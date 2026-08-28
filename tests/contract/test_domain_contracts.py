"""Contract-first invariants: UTC, identity, PM3 namespaces, risk gate shape."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.execution import OrderRequest
from botmoduleproject1.contracts.v1.forecasting import ForecastOutput, ModelVersionInfo, QuantileSet
from botmoduleproject1.contracts.v1.identity import SCHEMA_VERSION, EventEnvelope
from botmoduleproject1.contracts.v1.market import Tick
from botmoduleproject1.contracts.v1.risk import RiskVerdict, RiskVerdictStatus
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType, TradeIntent
from botmoduleproject1.contracts.v1.time import UTC, utc_now
import botmoduleproject1.contracts.v1.forecasting as forecasting_ns
import botmoduleproject1.contracts.v1.strategy as strategy_ns


def test_schema_version_v1() -> None:
    assert SCHEMA_VERSION == "v1"


def test_naive_datetime_rejected() -> None:
    naive = datetime(2026, 8, 28, 8, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        Tick(symbol="EURUSD", bid="1.1", ask="1.1001", timestamp=naive)


def test_event_envelope_identity() -> None:
    event = EventEnvelope(event_type="lifecycle", producer="pm1_platform")
    assert event.event_id
    assert event.correlation_id
    assert event.occurred_at.tzinfo is not None
    assert event.occurred_at.utcoffset() is not None
    assert event.schema_version == "v1"


def test_trade_intent_requires_idempotency_key() -> None:
    with pytest.raises(ValidationError):
        TradeIntent(
            occurred_at=utc_now(),
            symbol="EURUSD",
            direction=Direction.BUY,
            entry_type=EntryType.MARKET,
            idempotency_key="  ",
        )


def test_order_request_requires_risk_verdict_id() -> None:
    with pytest.raises(ValidationError):
        OrderRequest(
            causation_id=uuid4(),
            idempotency_key="k",
            occurred_at=utc_now(),
            intent_id=uuid4(),
            symbol="EURUSD",
            direction=Direction.BUY,
            entry_type=EntryType.MARKET,
            volume="0.1",
        )


def test_risk_verdict_allow_is_explicit() -> None:
    verdict = RiskVerdict(
        intent_id=uuid4(),
        occurred_at=utc_now(),
        status=RiskVerdictStatus.DENY,
    )
    assert verdict.allows_execution is False
    allowed = verdict.model_copy(update={"status": RiskVerdictStatus.ALLOW})
    assert allowed.allows_execution is True


def test_pm3_namespaces_are_distinct() -> None:
    assert strategy_ns.__name__.endswith("strategy")
    assert forecasting_ns.__name__.endswith("forecasting")
    assert hasattr(strategy_ns, "TradeIntent")
    assert hasattr(forecasting_ns, "ForecastOutput")
    assert not hasattr(strategy_ns, "ForecastOutput")
    assert not hasattr(forecasting_ns, "TradeIntent")


def test_forecast_output_shape() -> None:
    forecast = ForecastOutput(
        forecast_id=uuid4(),
        intent_id=uuid4(),
        event_id=uuid4(),
        correlation_id=uuid4(),
        occurred_at=utc_now(),
        symbol="EURUSD",
        horizon_bars=12,
        quantiles=QuantileSet(q05="1", q25="1", q50="1", q75="1", q95="1"),
        model=ModelVersionInfo(model_id="qrf", version="none"),
    )
    assert forecast.producer == "pm3_forecasting"
    assert forecast.occurred_at.tzinfo == UTC
