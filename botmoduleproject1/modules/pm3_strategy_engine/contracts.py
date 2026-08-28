"""Ports for the PM3-Strategy Engine. Implementations live in infrastructure."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from botmoduleproject1.contracts.v1.pm2 import PublicationBundle, RankedCandidate
from botmoduleproject1.contracts.v1.strategy import NoTradeDecision, TradeIntent
from botmoduleproject1.contracts.v1.strategy_engine import (
    StrategyFeedbackEvent,
    StrategyVote,
    SymbolConsensusResult,
    TrackerSnapshot,
    ValidationReport,
)
from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import (
    ProfileVersion,
    StrategyDraft,
    StrategyProfile,
    SymbolStrategyBinding,
)
from botmoduleproject1.modules.pm3_strategy_engine.domain.events import StrategyLifecycleEvent
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext


@runtime_checkable
class IStrategyTemplate(Protocol):
    template_type: object
    enabled_by_default: bool

    def evaluate(self, context: EvaluationContext) -> StrategyVote:
        ...


@runtime_checkable
class IConsensusPolicy(Protocol):
    def decide(
        self, votes: tuple[StrategyVote, ...], *, symbol: str, as_of: datetime
    ) -> SymbolConsensusResult:
        ...


@runtime_checkable
class ICalibrationPolicy(Protocol):
    version: str

    def calibrate(self, vote: StrategyVote) -> StrategyVote:
        ...


@runtime_checkable
class IBayesianUpdatePolicy(Protocol):
    enabled: bool

    def update(self, prior: float, evidence: float) -> float:
        ...


@runtime_checkable
class IHealthPolicy(Protocol):
    def evaluate(self, tracker: TrackerSnapshot, *, invalid: bool, stale_feedback: bool):
        ...


@runtime_checkable
class IVersioningPolicy(Protocol):
    def may_edit(self, version: ProfileVersion) -> bool:
        ...

    def may_activate(self, version: ProfileVersion) -> bool:
        ...


@runtime_checkable
class IProfileRepository(Protocol):
    def get(self, profile_id: str) -> StrategyProfile | None:
        ...

    def save(self, profile: StrategyProfile) -> None:
        ...

    def list_all(self) -> tuple[StrategyProfile, ...]:
        ...


@runtime_checkable
class IVersionRepository(Protocol):
    def get(self, version_id: str) -> ProfileVersion | None:
        ...

    def save(self, version: ProfileVersion) -> None:
        ...

    def list_for_profile(self, profile_id: str) -> tuple[ProfileVersion, ...]:
        ...


@runtime_checkable
class IBindingRepository(Protocol):
    def list_for_symbol(self, symbol: str) -> tuple[SymbolStrategyBinding, ...]:
        ...

    def save(self, binding: SymbolStrategyBinding) -> None:
        ...

    def list_all(self) -> tuple[SymbolStrategyBinding, ...]:
        ...

    def get(self, binding_id: str) -> SymbolStrategyBinding | None:
        ...


@runtime_checkable
class ITrackerRepository(Protocol):
    def get(self, profile_id: str, version_id: str) -> TrackerSnapshot | None:
        ...

    def save(self, snapshot: TrackerSnapshot) -> None:
        ...


@runtime_checkable
class IDraftRepository(Protocol):
    def get(self, draft_id: str) -> StrategyDraft | None:
        ...

    def save(self, draft: StrategyDraft) -> None:
        ...


@runtime_checkable
class IStrategyEventPublisher(Protocol):
    def publish(self, event: StrategyLifecycleEvent) -> None:
        ...


@runtime_checkable
class IPM2ContextAdapter(Protocol):
    def from_candidate(
        self,
        candidate: RankedCandidate,
        *,
        profile_id: str,
        version_id: str,
        params: dict,
        stale_ttl_hours: int,
    ) -> EvaluationContext:
        ...


@runtime_checkable
class IStrategyManifestProvider(Protocol):
    def manifest(self) -> dict:
        ...


@runtime_checkable
class IIntentSink(Protocol):
    def remember(self, key: str, artifact: TradeIntent | NoTradeDecision) -> bool:
        """Return False if duplicate."""
        ...
