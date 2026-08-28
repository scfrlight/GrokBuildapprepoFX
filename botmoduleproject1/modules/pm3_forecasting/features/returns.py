"""Confirmed-bar close-to-close returns. No lookahead."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.market import OhlcvBar
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class LookaheadError(ValueError):
    """A bar ends at or after the inference as_of."""


class MalformedBarsError(ValueError):
    """Empty, unsorted, mixed, or non-positive bars."""


def bar_end(bar: OhlcvBar) -> datetime:
    return bar.broker_as_of or bar.open_time


def assert_no_lookahead(bars: tuple[OhlcvBar, ...], as_of: datetime) -> None:
    """Raise if any bar is forming or from the future relative to as_of.

    Confirmed bars may *end* at as_of (just closed). Bars whose open_time
    is >= as_of, or whose broker_as_of is after as_of, are lookahead.
    """
    stamp = ensure_aware_utc(as_of, "as_of")
    for bar in bars:
        open_time = ensure_aware_utc(bar.open_time, "open_time")
        if open_time >= stamp:
            raise LookaheadError("lookahead: bar open_time >= as_of")
        end = bar.broker_as_of
        if end is not None:
            end = ensure_aware_utc(end, "broker_as_of")
            if end > stamp:
                raise LookaheadError("lookahead: bar ends after as_of")


def confirmed_bars(bars: tuple[OhlcvBar, ...], as_of: datetime) -> tuple[OhlcvBar, ...]:
    """Return bars fully confirmed before/at as_of, in chronological order."""
    if not bars:
        raise MalformedBarsError("empty bars")
    stamp = ensure_aware_utc(as_of, "as_of")
    kept: list[OhlcvBar] = []
    prev_open: datetime | None = None
    symbol = bars[0].symbol
    timeframe = bars[0].timeframe
    for bar in bars:
        if bar.symbol != symbol:
            raise MalformedBarsError("mixed symbols")
        if bar.timeframe != timeframe:
            raise MalformedBarsError("mixed timeframes")
        open_time = ensure_aware_utc(bar.open_time, "open_time")
        if prev_open is not None and open_time <= prev_open:
            raise MalformedBarsError("bars are not strictly increasing by open_time")
        prev_open = open_time
        if bar.close <= 0 or bar.open <= 0:
            raise MalformedBarsError("non-positive OHLC")
        end = bar.broker_as_of
        if end is not None:
            end = ensure_aware_utc(end, "broker_as_of")
            if end > stamp:
                raise LookaheadError("lookahead: forming bar")
        if open_time >= stamp:
            raise LookaheadError("lookahead: bar open_time >= as_of")
        kept.append(bar)
    if not kept:
        raise MalformedBarsError("no confirmed bars")
    return tuple(kept)


def close_to_close_returns(bars: tuple[OhlcvBar, ...]) -> tuple[Decimal, ...]:
    """Simple returns r[t] = close[t] / close[t-1] - 1. Confirmed bars only."""
    if len(bars) < 2:
        return ()
    out: list[Decimal] = []
    for i in range(1, len(bars)):
        prev = bars[i - 1].close
        if prev <= 0:
            raise MalformedBarsError("non-positive close")
        out.append(bars[i].close / prev - Decimal("1"))
    return tuple(out)
