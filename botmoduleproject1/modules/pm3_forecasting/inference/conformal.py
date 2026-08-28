"""In-memory conformal coverage tracker. Insufficient data ≠ healthy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.modules.pm3_forecasting.domain.policies import coverage_healthy

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


@dataclass(frozen=True)
class CoverageObservation:
    forecast_id: object
    symbol: str
    inside_90: bool
    inside_50: bool
    realized_close: Decimal
    realized_open_time: datetime


@dataclass
class PendingForecast:
    forecast_id: object
    symbol: str
    last_open_time: datetime
    horizon_bars: int
    timeframe: Timeframe
    q05: Decimal
    q25: Decimal
    q75: Decimal
    q95: Decimal


@dataclass
class ConformalTracker:
    min_coverage_samples: int = 20
    _pending: list[PendingForecast] = field(default_factory=list)
    _observations: list[CoverageObservation] = field(default_factory=list)

    def register(
        self,
        forecast: ForecastOutput,
        *,
        last_open_time: datetime,
        timeframe: Timeframe,
    ) -> None:
        q = forecast.quantiles
        self._pending.append(
            PendingForecast(
                forecast_id=forecast.forecast_id,
                symbol=forecast.symbol,
                last_open_time=last_open_time,
                horizon_bars=forecast.horizon_bars,
                timeframe=timeframe,
                q05=q.q05,
                q25=q.q25,
                q75=q.q75,
                q95=q.q95,
            )
        )

    def realize(self, bars: tuple[OhlcvBar, ...]) -> int:
        """Consume pending forecasts whose horizon bar is now confirmed."""
        if not bars or not self._pending:
            return 0
        by_open = {b.open_time: b for b in bars}
        still: list[PendingForecast] = []
        realized = 0
        for pending in self._pending:
            target = pending.last_open_time + timedelta(
                minutes=_TF_MINUTES[pending.timeframe] * pending.horizon_bars
            )
            bar = by_open.get(target)
            if bar is None or bar.symbol != pending.symbol:
                still.append(pending)
                continue
            close = bar.close
            self._observations.append(
                CoverageObservation(
                    forecast_id=pending.forecast_id,
                    symbol=pending.symbol,
                    inside_90=pending.q05 <= close <= pending.q95,
                    inside_50=pending.q25 <= close <= pending.q75,
                    realized_close=close,
                    realized_open_time=bar.open_time,
                )
            )
            realized += 1
        self._pending = still
        return realized

    @property
    def sample_size(self) -> int:
        return len(self._observations)

    def coverage_90(self) -> float | None:
        if not self._observations:
            return None
        hits = sum(1 for o in self._observations if o.inside_90)
        return hits / float(len(self._observations))

    def coverage_50(self) -> float | None:
        if not self._observations:
            return None
        hits = sum(1 for o in self._observations if o.inside_50)
        return hits / float(len(self._observations))

    def healthy(self) -> bool:
        return coverage_healthy(self.sample_size, self.min_coverage_samples)

    def snapshot(self) -> dict[str, object]:
        return {
            "sample_size": self.sample_size,
            "pending": len(self._pending),
            "coverage_90": self.coverage_90(),
            "coverage_50": self.coverage_50(),
            "healthy": self.healthy(),
        }
