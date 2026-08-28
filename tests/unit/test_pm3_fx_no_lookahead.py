"""Walk-forward splitter never uses future or forming bars."""

from __future__ import annotations

from datetime import timedelta

from botmoduleproject1.modules.pm3_forecasting.features.returns import LookaheadError, confirmed_bars
from botmoduleproject1.modules.pm3_forecasting.research.splitter import walk_forward_samples
from tests.unit.pm3fx_support import AS_OF, confirmed_bars as synth_bars, forecasting_module, make_intent


def test_walk_forward_end_strictly_before_as_of() -> None:
    bars = synth_bars(count=80)
    samples = walk_forward_samples(
        bars, horizon_bars=4, embargo_bars=1, as_of=AS_OF
    )
    assert samples
    last_index = len(bars) - 1
    for sample in samples:
        assert sample.end_open_time < AS_OF
        assert sample.start_open_time < AS_OF
        assert sample.end_index <= last_index - 1
        assert sample.end_index == sample.start_index + 4
        assert bars[sample.end_index].open_time < AS_OF
        assert bars[sample.end_index].open_time <= bars[last_index].open_time


def test_embargo_excludes_last_confirmed_bar_as_window_end() -> None:
    bars = synth_bars(count=80)
    samples = walk_forward_samples(
        bars, horizon_bars=4, embargo_bars=1, as_of=AS_OF
    )
    last_index = len(bars) - 1
    assert all(s.end_index < last_index for s in samples)
    assert max(s.end_index for s in samples) == last_index - 1


def test_future_bar_fail_closed_none() -> None:
    bars = list(synth_bars(count=80))
    future = bars[-1].model_copy(
        update={
            "open_time": AS_OF + timedelta(hours=1),
            "broker_as_of": AS_OF + timedelta(hours=2),
        }
    )
    mod = forecasting_module()
    assert mod.forecast_with_bars(make_intent(key="future"), tuple(bars + [future])) is None


def test_forming_bar_fail_closed_none() -> None:
    bars = list(synth_bars(count=80))
    forming = bars[-1].model_copy(
        update={
            "open_time": AS_OF - timedelta(minutes=30),
            "broker_as_of": AS_OF + timedelta(minutes=30),
        }
    )
    mod = forecasting_module()
    assert mod.forecast_with_bars(make_intent(key="forming"), tuple(bars + [forming])) is None


def test_confirmed_bars_rejects_lookahead() -> None:
    bars = list(synth_bars(count=8))
    future = bars[-1].model_copy(update={"open_time": AS_OF})
    try:
        confirmed_bars(tuple(bars[:-1] + [future]), AS_OF)
        raised = False
    except LookaheadError:
        raised = True
    assert raised is True
