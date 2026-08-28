"""PM3 forecasting / QRF v1 contract invariants."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput, ModelVersionInfo, QuantileSet
from botmoduleproject1.contracts.v1.time import UTC, utc_now


def test_quantile_set_rejects_inversion() -> None:
    with pytest.raises(ValidationError, match="non-decreasing"):
        QuantileSet(q05="2", q25="1", q50="1.1", q75="1.2", q95="1.3")


def test_quantile_set_allows_equal_values() -> None:
    qs = QuantileSet(q05="1", q25="1", q50="1", q75="1", q95="1")
    assert qs.q05 == qs.q95


def test_quantile_set_accepts_strictly_ordered() -> None:
    qs = QuantileSet(q05="1.0", q25="1.1", q50="1.2", q75="1.3", q95="1.4")
    assert qs.q05 < qs.q25 < qs.q50 < qs.q75 < qs.q95


def test_forecast_output_utc_and_producer() -> None:
    forecast = ForecastOutput(
        forecast_id=uuid4(),
        intent_id=uuid4(),
        event_id=uuid4(),
        correlation_id=uuid4(),
        occurred_at=utc_now(),
        symbol="EURUSD",
        horizon_bars=4,
        quantiles=QuantileSet(q05="1", q25="1", q50="1", q75="1", q95="1"),
        model=ModelVersionInfo(model_id="residual_quantile_envelope", version="0.1.0"),
    )
    assert forecast.producer == "pm3_forecasting"
    assert forecast.occurred_at.tzinfo == UTC
    assert forecast.coverage is None
    assert forecast.sample_size is None


def test_forecast_output_rejects_naive_occurred_at() -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        ForecastOutput(
            forecast_id=uuid4(),
            intent_id=uuid4(),
            event_id=uuid4(),
            correlation_id=uuid4(),
            occurred_at=naive,
            symbol="EURUSD",
            horizon_bars=4,
            quantiles=QuantileSet(q05="1", q25="1", q50="1", q75="1", q95="1"),
            model=ModelVersionInfo(model_id="residual_quantile_envelope", version="0.1.0"),
        )
