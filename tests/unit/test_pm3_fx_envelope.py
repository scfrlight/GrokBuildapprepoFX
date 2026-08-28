"""Residual quantile envelope: ordering, FX 5dp, min_samples fail-closed."""

from __future__ import annotations

from decimal import Decimal

from tests.unit.pm3fx_support import confirmed_bars, forecasting_module, make_intent

QUANTUM = Decimal("0.00001")


def test_ordered_quantiles_and_five_decimal_places() -> None:
    mod = forecasting_module()
    out = mod.forecast_with_bars(make_intent(key="env-1"), confirmed_bars())
    assert out is not None
    q = out.quantiles
    assert q.q05 <= q.q25 <= q.q50 <= q.q75 <= q.q95
    for value in (q.q05, q.q25, q.q50, q.q75, q.q95):
        assert value == value.quantize(QUANTUM)
        assert value.as_tuple().exponent == -5
    assert out.model.model_id == "residual_quantile_envelope"
    assert out.model.version == "0.1.0"
    assert out.producer == "pm3_forecasting"
    assert out.diagnostics.get("not_fitted_qrf") is True
    assert out.sample_size is not None and out.sample_size >= 20
    assert out.horizon_seconds == 4 * 3600


def test_min_samples_returns_none() -> None:
    mod = forecasting_module()
    short = confirmed_bars(count=16)
    assert mod.forecast_with_bars(make_intent(key="short"), short) is None


def test_empty_bars_return_none() -> None:
    mod = forecasting_module()
    assert mod.forecast_with_bars(make_intent(key="empty"), ()) is None


def test_blank_symbol_returns_none() -> None:
    mod = forecasting_module()
    intent = make_intent(symbol="   ", key="blank")
    assert mod.forecast_with_bars(intent, confirmed_bars()) is None


def test_model_trained_at_is_as_of() -> None:
    mod = forecasting_module()
    intent = make_intent(key="trained")
    out = mod.forecast_with_bars(intent, confirmed_bars())
    assert out is not None
    assert out.model.trained_at == intent.occurred_at
    assert out.correlation_id == intent.correlation_id
    assert out.causation_id == intent.event_id
    assert out.intent_id == intent.intent_id
