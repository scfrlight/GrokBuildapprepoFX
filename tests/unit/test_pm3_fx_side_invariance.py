"""LONG and SHORT intents with the same bars produce identical quantiles."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy import Direction
from tests.unit.pm3fx_support import confirmed_bars, forecasting_module, make_intent


def test_buy_and_sell_identical_quantiles() -> None:
    bars = confirmed_bars()
    mod = forecasting_module()
    buy = mod.forecast_with_bars(make_intent(direction=Direction.BUY, key="buy"), bars)
    sell = mod.forecast_with_bars(make_intent(direction=Direction.SELL, key="sell"), bars)
    assert buy is not None
    assert sell is not None
    assert buy.quantiles == sell.quantiles
    assert buy.sample_size == sell.sample_size
    assert buy.horizon_bars == sell.horizon_bars
    assert buy.diagnostics.get("side_invariant") is True


def test_direction_is_not_a_vote() -> None:
    bars = confirmed_bars()
    mod = forecasting_module()
    out = mod.forecast_with_bars(make_intent(direction=Direction.BUY, key="vote"), bars)
    assert out is not None
    blob = str(out.model_dump())
    assert "GO_LONG" not in blob
    assert "GO_SHORT" not in blob
    assert out.quantiles.q50 is not None
