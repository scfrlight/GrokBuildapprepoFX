"""Intent → ForecastOutput. Does not mutate side. Does not create intents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput, ModelVersionInfo
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.strategy import TradeIntent
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.modules.pm3_forecasting.config.schema import Pm3ForecastingConfig
from botmoduleproject1.modules.pm3_forecasting.domain.ids import new_event_id, new_forecast_id
from botmoduleproject1.modules.pm3_forecasting.domain.policies import MODEL_ID, MODEL_VERSION, is_blank_symbol
from botmoduleproject1.modules.pm3_forecasting.features.returns import (
    LookaheadError,
    MalformedBarsError,
    confirmed_bars,
)
from botmoduleproject1.modules.pm3_forecasting.inference.conformal import ConformalTracker
from botmoduleproject1.modules.pm3_forecasting.inference.envelope import envelope
from botmoduleproject1.modules.pm3_forecasting.publication.publisher import ForecastPublisher
from botmoduleproject1.modules.pm3_forecasting.registry.memory import InMemoryModelRegistry
from botmoduleproject1.modules.pm3_forecasting.research.splitter import forward_returns, walk_forward_samples

_TF_SECONDS = {
    Timeframe.M1: 60,
    Timeframe.M5: 300,
    Timeframe.M15: 900,
    Timeframe.M30: 1800,
    Timeframe.H1: 3600,
    Timeframe.H4: 14400,
    Timeframe.D1: 86400,
    Timeframe.W1: 604800,
}


class ForecastEnrichment:
    """Maps a TradeIntent plus confirmed bars to an optional ForecastOutput."""

    def __init__(
        self,
        config: Pm3ForecastingConfig,
        *,
        registry: InMemoryModelRegistry,
        tracker: ConformalTracker,
        publisher: ForecastPublisher,
    ) -> None:
        self.config = config
        self.registry = registry
        self.tracker = tracker
        self.publisher = publisher
        self._cache: dict[str, ForecastOutput] = {}

    def enrich(
        self,
        intent: TradeIntent,
        bars: tuple[OhlcvBar, ...],
        *,
        as_of: datetime | None = None,
        timeframe: Timeframe = Timeframe.H1,
    ) -> ForecastOutput | None:
        try:
            stamp = ensure_aware_utc(as_of or intent.occurred_at, "as_of")
        except (TypeError, ValueError):
            return None
        if is_blank_symbol(intent.symbol):
            return None
        cached = self._cache.get(intent.idempotency_key)
        if cached is not None:
            return cached
        try:
            confirmed = confirmed_bars(bars, stamp)
        except (LookaheadError, MalformedBarsError, TypeError, ValueError):
            return None
        try:
            samples = walk_forward_samples(
                confirmed,
                horizon_bars=self.config.horizon_bars,
                embargo_bars=self.config.embargo_bars,
                as_of=stamp,
            )
        except (LookaheadError, ValueError):
            return None
        rets = forward_returns(samples)
        if len(rets) < self.config.min_samples:
            return None
        last = confirmed[-1]
        quantiles = envelope(rets, last.close)
        if quantiles is None:
            return None
        model = self.registry.register(
            ModelVersionInfo(
                model_id=MODEL_ID,
                version=MODEL_VERSION,
                trained_at=stamp,
            )
        )
        coverage = self.tracker.coverage_90()
        diagnostics: dict[str, Any] = {
            "estimator": MODEL_ID,
            "not_fitted_qrf": True,
            "sample_size": len(rets),
            "lookback_bars": len(confirmed),
            "embargo_bars": self.config.embargo_bars,
            "side_invariant": True,
            "observe_only": True,
            "operating_mode": self.config.operating_mode,
            "direction_ignored": getattr(intent.direction, "value", str(intent.direction)),
        }
        output = ForecastOutput(
            forecast_id=new_forecast_id(),
            intent_id=intent.intent_id,
            event_id=new_event_id(),
            correlation_id=intent.correlation_id,
            causation_id=intent.event_id,
            occurred_at=stamp,
            symbol=intent.symbol,
            horizon_bars=self.config.horizon_bars,
            quantiles=quantiles,
            model=model,
            producer="pm3_forecasting",
            coverage=coverage,
            sample_size=len(rets),
            horizon_seconds=self.config.horizon_bars * _TF_SECONDS[timeframe],
            diagnostics=diagnostics,
        )
        self.tracker.register(output, last_open_time=last.open_time, timeframe=timeframe)
        self.tracker.realize(confirmed)
        self.publisher.publish(output)
        self._cache[intent.idempotency_key] = output
        return output
