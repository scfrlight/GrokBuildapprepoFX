"""Shared fixtures for PM3 forecasting / QRF tests. Not a package."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.adapters.market.synthetic import generate_bars
from botmoduleproject1.contracts.v1.market import Timeframe
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType, TradeIntent
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm3_forecasting.config.schema import Pm3ForecastingConfig
from botmoduleproject1.modules.pm3_forecasting.module import PM3ForecastingModule

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


class _Clock:
    def __init__(self, instant: datetime = AS_OF) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


def make_intent(
    *,
    direction: Direction = Direction.BUY,
    symbol: str = "EURUSD",
    key: str = "fx-1",
    occurred_at: datetime = AS_OF,
) -> TradeIntent:
    return TradeIntent(
        idempotency_key=key,
        occurred_at=occurred_at,
        symbol=symbol,
        direction=direction,
        entry_type=EntryType.MARKET,
        requested_volume=None,
    )


def confirmed_bars(
    symbol: str = "EURUSD",
    count: int = 80,
    as_of: datetime = AS_OF,
    timeframe: Timeframe = Timeframe.H1,
) -> tuple:
    return generate_bars(symbol, timeframe, count=count, as_of=as_of)


def forecasting_module(
    config: Pm3ForecastingConfig | None = None, enabled: bool = True
) -> PM3ForecastingModule:
    cfg = config or Pm3ForecastingConfig()
    return PM3ForecastingModule(cfg, _Clock(), feature_enabled=enabled)
