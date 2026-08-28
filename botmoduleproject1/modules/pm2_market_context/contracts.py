"""Stable Protocol interfaces for PM2. Versioned via contracts/v1."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.pm2 import (
    CandidateScoreCard,
    PublicationBundle,
    RankedCandidate,
    SuppressionRecord,
)
from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot
from botmoduleproject1.modules.pm2_market_context.scanner.universe_scanner import SymbolSnapshot


@runtime_checkable
class UniverseScannerPort(Protocol):
    def scan(self, as_of: datetime) -> tuple[SymbolSnapshot, ...]:
        ...


@runtime_checkable
class FeatureBuilderPort(Protocol):
    def __call__(
        self,
        symbol: str,
        timeframe: Timeframe,
        bars: tuple[OhlcvBar, ...],
        as_of: datetime,
    ) -> FeatureSnapshot:
        ...


@runtime_checkable
class RegimeEnginePort(Protocol):
    def evaluate(self, snapshot: FeatureSnapshot, as_of: datetime) -> object:
        ...


@runtime_checkable
class ContextEnginePort(Protocol):
    def evaluate(self, *args: object, **kwargs: object) -> object:
        ...


@runtime_checkable
class ConfluenceScorerPort(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> CandidateScoreCard:
        ...


@runtime_checkable
class QualificationStateMachinePort(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> object:
        ...


@runtime_checkable
class CandidateRankerPort(Protocol):
    def rank(
        self,
        candidates: tuple[RankedCandidate, ...],
        *,
        as_of: datetime,
    ) -> tuple[RankedCandidate, ...]:
        ...


@runtime_checkable
class CorrelationSuppressorPort(Protocol):
    def __call__(
        self,
        ranked: tuple[RankedCandidate, ...],
        config: object,
    ) -> tuple[tuple[RankedCandidate, ...], tuple[SuppressionRecord, ...]]:
        ...


@runtime_checkable
class PublicationGatewayPort(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> PublicationBundle:
        ...


@runtime_checkable
class AttributionRecorderPort(Protocol):
    def __call__(self, candidate: RankedCandidate) -> dict[str, object]:
        ...


@runtime_checkable
class CalibrationTrackerPort(Protocol):
    def __call__(self, candidates: tuple[RankedCandidate, ...]) -> dict[str, object]:
        ...


@runtime_checkable
class HealthContributorPort(Protocol):
    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        ...


@runtime_checkable
class PM2ModulePort(Protocol):
    def metadata(self) -> ModuleMetadata:
        ...

    def latest_bar(self, symbol: str, timeframe: Timeframe) -> OhlcvBar | None:
        ...

    def scan(self, as_of: datetime | None = None) -> PublicationBundle:
        ...
