"""Walk-forward splitter with embargo. No lookahead into inference time T."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.market import OhlcvBar
from botmoduleproject1.modules.pm3_forecasting.features.returns import LookaheadError, bar_end


@dataclass(frozen=True)
class ForwardSample:
    """One walk-forward observation. End bar is strictly before inference T."""

    start_index: int
    end_index: int
    start_open_time: datetime
    end_open_time: datetime
    forward_return: Decimal


def walk_forward_samples(
    bars: tuple[OhlcvBar, ...],
    *,
    horizon_bars: int,
    embargo_bars: int,
    as_of: datetime,
) -> tuple[ForwardSample, ...]:
    """Historical horizon-bar forward returns with embargo.

    For training sample at index ``i`` the forward return is
    ``close[i+horizon] / close[i] - 1``. Inference at time ``T`` (``as_of``)
    may only use samples with ``(i + horizon) < T`` (no lookahead). Embargo
    of at least one bar means the last confirmed close (index ``L``, the
    mapping price) is not a forward-window endpoint:

    ``i_max = L - horizon_bars - embargo_bars``.
    """
    if horizon_bars < 1:
        return ()
    if embargo_bars < 1:
        raise LookaheadError("embargo_bars must be >= 1")
    last_index = len(bars) - 1
    i_max = last_index - horizon_bars - embargo_bars
    if i_max < 0:
        return ()
    samples: list[ForwardSample] = []
    for i in range(0, i_max + 1):
        start = bars[i]
        end = bars[i + horizon_bars]
        if start.close <= 0:
            continue
        if end.open_time >= as_of:
            raise LookaheadError("lookahead: forward window open_time >= as_of")
        if bar_end(end) > as_of:
            raise LookaheadError("lookahead: forward window ends after as_of")
        # end_index must stay embargo bars before last confirmed index
        if i + horizon_bars > last_index - embargo_bars:
            raise LookaheadError("lookahead: sample violates embargo")
        fwd = end.close / start.close - Decimal("1")
        samples.append(
            ForwardSample(
                start_index=i,
                end_index=i + horizon_bars,
                start_open_time=start.open_time,
                end_open_time=end.open_time,
                forward_return=fwd,
            )
        )
    return tuple(samples)


def forward_returns(samples: tuple[ForwardSample, ...]) -> tuple[Decimal, ...]:
    return tuple(s.forward_return for s in samples)
