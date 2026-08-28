"""Deterministic synthetic OHLCV. No broker. Confirmed bars only."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.time import UTC

_TF_MINUTES = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.M30: 30,
    Timeframe.H1: 60,
    Timeframe.H4: 240,
    Timeframe.D1: 1440,
    Timeframe.W1: 10080,
}


def _seed_bytes(symbol: str, salt: int) -> bytes:
    return hashlib.sha256(f"{symbol}:{salt}".encode("utf-8")).digest()


def generate_bars(
    symbol: str,
    timeframe: Timeframe,
    *,
    count: int,
    as_of: datetime,
    salt: int = 1,
) -> tuple[OhlcvBar, ...]:
    """Return ``count`` *confirmed* bars ending before ``as_of``."""
    minutes = _TF_MINUTES[timeframe]
    step = timedelta(minutes=minutes)
    aligned = as_of.replace(second=0, microsecond=0)
    remainder = aligned.minute % minutes if timeframe not in {Timeframe.H1, Timeframe.H4, Timeframe.D1, Timeframe.W1} else 0
    if timeframe is Timeframe.H1:
        aligned = aligned.replace(minute=0)
    elif timeframe is Timeframe.H4:
        aligned = aligned.replace(minute=0, hour=(aligned.hour // 4) * 4)
    elif timeframe in {Timeframe.D1, Timeframe.W1}:
        aligned = aligned.replace(hour=0, minute=0)
    else:
        aligned = aligned.replace(minute=aligned.minute - remainder)
    last_open = aligned - step  # confirmed: last closed bar
    seed = _seed_bytes(symbol, salt)
    base = 1.05000 + (seed[0] / 255.0) * 0.40000
    bars: list[OhlcvBar] = []
    price = base
    for i in range(count):
        open_time = last_open - step * (count - 1 - i)
        noise = ((seed[i % len(seed)] / 127.5) - 1.0) * 0.0008
        drift = 0.00005 * (1 if seed[(i + 3) % len(seed)] % 2 == 0 else -1)
        open_px = price
        close_px = max(0.1, open_px + drift + noise)
        high_px = max(open_px, close_px) + abs(noise) * 0.4
        low_px = min(open_px, close_px) - abs(noise) * 0.4
        volume = Decimal(str(100 + (seed[i % len(seed)] % 50)))
        bars.append(
            OhlcvBar(
                symbol=symbol,
                timeframe=timeframe,
                open_time=open_time if open_time.tzinfo else open_time.replace(tzinfo=UTC),
                open=Decimal(str(round(open_px, 5))),
                high=Decimal(str(round(high_px, 5))),
                low=Decimal(str(round(low_px, 5))),
                close=Decimal(str(round(close_px, 5))),
                volume=volume,
                broker_as_of=open_time + step,
            )
        )
        price = close_px
    return tuple(bars)


class SyntheticMarketFeed:
    """In-memory confirmed-bar feed. Pair-agnostic. No lookahead."""

    def __init__(self, *, as_of: datetime, lookback: int = 64, salt: int = 1) -> None:
        self.as_of = as_of
        self.lookback = lookback
        self.salt = salt

    def bars(self, symbol: str, timeframe: Timeframe) -> tuple[OhlcvBar, ...]:
        return generate_bars(
            symbol, timeframe, count=self.lookback, as_of=self.as_of, salt=self.salt
        )

    def latest_bar(self, symbol: str, timeframe: Timeframe) -> OhlcvBar | None:
        series = self.bars(symbol, timeframe)
        return series[-1] if series else None
