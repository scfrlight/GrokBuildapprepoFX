"""Multi-timeframe alignment: decision TF is the clock; others must end at or before it."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.market import OhlcvBar


def last_confirmed(bars: tuple[OhlcvBar, ...]) -> OhlcvBar | None:
    return bars[-1] if bars else None


def aligned(decision: tuple[OhlcvBar, ...], other: tuple[OhlcvBar, ...]) -> bool:
    if not decision or not other:
        return False
    d_end = decision[-1].broker_as_of or decision[-1].open_time
    o_end = other[-1].broker_as_of or other[-1].open_time
    return o_end <= d_end
