"""Pure-Python bar statistics. No numpy. Confirmed bars only."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.market import OhlcvBar


def closes(bars: tuple[OhlcvBar, ...]) -> tuple[float, ...]:
    return tuple(float(b.close) for b in bars)


def sma(values: tuple[float, ...], window: int) -> float:
    if window <= 0 or len(values) < window:
        return values[-1] if values else 0.0
    chunk = values[-window:]
    return sum(chunk) / float(window)


def roc(values: tuple[float, ...], window: int) -> float:
    if len(values) <= window or values[-1 - window] == 0:
        return 0.0
    return (values[-1] - values[-1 - window]) / abs(values[-1 - window])


def atr(bars: tuple[OhlcvBar, ...], window: int = 14) -> float:
    if len(bars) < 2:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(bars)):
        high = float(bars[i].high)
        low = float(bars[i].low)
        prev_close = float(bars[i - 1].close)
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    use = trs[-window:] if len(trs) >= window else trs
    return sum(use) / float(len(use)) if use else 0.0


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def scale_unit(value: float, *, gain: float = 100.0) -> float:
    """Map roughly [-1, 1] evidence into 0–100."""
    return clamp(50.0 + value * gain)


def assert_no_lookahead(bars: tuple[OhlcvBar, ...], as_of_ts: float) -> None:
    for bar in bars:
        end = bar.broker_as_of or bar.open_time
        if end.timestamp() > as_of_ts:
            raise ValueError("lookahead: bar ends after decision as_of")
