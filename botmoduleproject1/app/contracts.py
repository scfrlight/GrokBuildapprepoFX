"""Provider ports. Implementations live in adapters or future PM modules."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1 import (
    AlertEvent,
    ExecutionReport,
    ExposureSnapshot,
    ForecastOutput,
    JournalEntry,
    OhlcvBar,
    OrderRequest,
    RiskVerdict,
    SignalEvent,
    Timeframe,
    TradeIntent,
)


@runtime_checkable
class ClockPort(Protocol):
    def now(self) -> datetime:
        ...


@runtime_checkable
class ModuleMetadataProvider(Protocol):
    def metadata(self) -> ModuleMetadata:
        ...


@runtime_checkable
class HealthCheckProvider(Protocol):
    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        ...


@runtime_checkable
class MarketDataProvider(Protocol):
    def latest_bar(self, symbol: str, timeframe: Timeframe) -> OhlcvBar | None:
        ...


@runtime_checkable
class SignalProvider(Protocol):
    def latest_signal(self, symbol: str) -> SignalEvent | None:
        ...


@runtime_checkable
class ModelProvider(Protocol):
    def forecast(self, intent: TradeIntent) -> ForecastOutput | None:
        ...


@runtime_checkable
class RiskGate(Protocol):
    """Exclusive execution permission issuer (ADR-007)."""

    def is_ready(self) -> bool:
        ...

    def evaluate(self, intent: TradeIntent, exposure: ExposureSnapshot) -> RiskVerdict:
        ...


@runtime_checkable
class ExecutionProvider(Protocol):
    def submit(self, request: OrderRequest) -> ExecutionReport:
        ...


@runtime_checkable
class StorageProvider(Protocol):
    def append(self, entry: JournalEntry) -> None:
        ...


@runtime_checkable
class NotificationProvider(Protocol):
    def publish(self, alert: AlertEvent) -> None:
        ...


@runtime_checkable
class MonitoringProvider(Protocol):
    def observe(self, entry: JournalEntry) -> None:
        ...


# Spec alias
RiskProvider = RiskGate

