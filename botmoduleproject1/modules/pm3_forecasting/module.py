"""PM3 forecasting / QRF orchestrator. Enrichment only. Not the Strategy Engine."""

from __future__ import annotations

from typing import Any

from botmoduleproject1.adapters.market.synthetic import generate_bars
from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.strategy import TradeIntent
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.modules.pm3_forecasting.application.enrichment import ForecastEnrichment
from botmoduleproject1.modules.pm3_forecasting.capabilities import PM3_FORECASTING_METADATA
from botmoduleproject1.modules.pm3_forecasting.config.schema import (
    Pm3ForecastingConfig,
    config_from_settings,
)
from botmoduleproject1.modules.pm3_forecasting.diagnostics.health import health_checks as fx_health
from botmoduleproject1.modules.pm3_forecasting.inference.conformal import ConformalTracker
from botmoduleproject1.modules.pm3_forecasting.publication.publisher import ForecastPublisher
from botmoduleproject1.modules.pm3_forecasting.registry.memory import InMemoryModelRegistry


class PM3ForecastingModule:
    """Registered as pm3_forecasting. Implements ModelProvider. Never orders."""

    def __init__(
        self,
        config: Pm3ForecastingConfig,
        clock: Any,
        *,
        feature_enabled: bool = True,
    ) -> None:
        self.config = config
        self.clock = clock
        self.feature_enabled = feature_enabled
        self.timeframe = Timeframe(config.timeframe)
        self.registry = InMemoryModelRegistry()
        self.tracker = ConformalTracker(min_coverage_samples=config.min_coverage_samples)
        self.publisher = ForecastPublisher()
        self.enrichment = ForecastEnrichment(
            config,
            registry=self.registry,
            tracker=self.tracker,
            publisher=self.publisher,
        )

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM3ForecastingModule:
        flag = bool(getattr(settings, "feature_flags").forecasting)
        return cls(config_from_settings(settings), clock, feature_enabled=flag)

    def metadata(self) -> ModuleMetadata:
        return PM3_FORECASTING_METADATA

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return fx_health(kind, feature_enabled=self.feature_enabled, tracker=self.tracker)

    def forecast(self, intent: TradeIntent) -> ForecastOutput | None:
        if not self.feature_enabled:
            return None
        try:
            as_of = ensure_aware_utc(intent.occurred_at, "occurred_at")
        except (TypeError, ValueError):
            return None
        try:
            bars = generate_bars(
                intent.symbol,
                self.timeframe,
                count=self.config.lookback_bars,
                as_of=as_of,
            )
        except (TypeError, ValueError, KeyError):
            return None
        return self.forecast_with_bars(intent, bars)

    def forecast_with_bars(
        self, intent: TradeIntent, bars: tuple[OhlcvBar, ...]
    ) -> ForecastOutput | None:
        if not self.feature_enabled:
            return None
        try:
            as_of = ensure_aware_utc(intent.occurred_at, "occurred_at")
        except (TypeError, ValueError):
            return None
        try:
            return self.enrichment.enrich(
                intent, bars, as_of=as_of, timeframe=self.timeframe
            )
        except (TypeError, ValueError):
            return None
