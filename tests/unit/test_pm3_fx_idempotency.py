"""Duplicate idempotency_key returns the cached ForecastOutput."""

from __future__ import annotations

from tests.unit.pm3fx_support import confirmed_bars, forecasting_module, make_intent


def test_duplicate_key_same_forecast_id() -> None:
    mod = forecasting_module()
    bars = confirmed_bars()
    first = make_intent(key="same-key")
    second = make_intent(key="same-key")
    a = mod.forecast_with_bars(first, bars)
    b = mod.forecast_with_bars(second, bars)
    assert a is not None
    assert b is not None
    assert a.forecast_id == b.forecast_id
    assert a.event_id == b.event_id
    assert a.quantiles == b.quantiles


def test_distinct_keys_distinct_forecast_ids() -> None:
    mod = forecasting_module()
    bars = confirmed_bars()
    a = mod.forecast_with_bars(make_intent(key="k-a"), bars)
    b = mod.forecast_with_bars(make_intent(key="k-b"), bars)
    assert a is not None and b is not None
    assert a.forecast_id != b.forecast_id
