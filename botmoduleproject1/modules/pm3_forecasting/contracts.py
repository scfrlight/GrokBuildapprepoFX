"""Module-local ports for PM3 forecasting / QRF. Implementations live beside them."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.forecasting import ForecastOutput, ModelVersionInfo, QuantileSet
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.strategy import TradeIntent


@runtime_checkable
class BarSource(Protocol):
    def bars(self, symbol: str, timeframe: Timeframe) -> tuple[OhlcvBar, ...]:
        ...


@runtime_checkable
class EnvelopeEstimator(Protocol):
    def estimate(
        self,
        forward_returns: tuple[object, ...],
        last_close: object,
    ) -> QuantileSet | None:
        ...


@runtime_checkable
class ModelRegistryPort(Protocol):
    def register(self, info: ModelVersionInfo) -> ModelVersionInfo:
        ...

    def get(self, model_id: str, version: str) -> ModelVersionInfo | None:
        ...


@runtime_checkable
class ForecastPublisherPort(Protocol):
    def publish(self, forecast: ForecastOutput) -> ForecastOutput:
        ...


@runtime_checkable
class EnrichmentPort(Protocol):
    def enrich(
        self, intent: TradeIntent, bars: tuple[OhlcvBar, ...], *, as_of: datetime
    ) -> ForecastOutput | None:
        ...


@runtime_checkable
class HealthContributorPort(Protocol):
    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        ...


@runtime_checkable
class PM3ForecastingModulePort(Protocol):
    def metadata(self) -> ModuleMetadata:
        ...

    def forecast(self, intent: TradeIntent) -> ForecastOutput | None:
        ...
