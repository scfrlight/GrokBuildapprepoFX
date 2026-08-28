"""PM3-Strategy Engine orchestrator. Headless. Observe-only. Not forecasting."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.pm2 import PublicationBundle, RankedCandidate
from botmoduleproject1.contracts.v1.signals import ConfluenceScore, SignalEvent
from botmoduleproject1.contracts.v1.strategy import Direction, NoTradeDecision, TradeIntent
from botmoduleproject1.contracts.v1.strategy_engine import StrategyFeedbackEvent
from botmoduleproject1.modules.pm3_strategy_engine.application.activation_service import ActivationService
from botmoduleproject1.modules.pm3_strategy_engine.application.binding_service import SymbolBindingService
from botmoduleproject1.modules.pm3_strategy_engine.application.calibration_service import CalibrationService
from botmoduleproject1.modules.pm3_strategy_engine.application.consensus_service import ConsensusService
from botmoduleproject1.modules.pm3_strategy_engine.application.control_bridge_service import (
    StrategyControlBridgeService,
)
from botmoduleproject1.modules.pm3_strategy_engine.application.draft_service import DraftService
from botmoduleproject1.modules.pm3_strategy_engine.application.health_service import HealthService
from botmoduleproject1.modules.pm3_strategy_engine.application.intent_service import IntentService
from botmoduleproject1.modules.pm3_strategy_engine.application.pm2_handoff_service import PM2HandoffService
from botmoduleproject1.modules.pm3_strategy_engine.application.profile_service import ProfileService
from botmoduleproject1.modules.pm3_strategy_engine.application.rollback_service import RollbackService
from botmoduleproject1.modules.pm3_strategy_engine.application.tracker_service import TrackerService
from botmoduleproject1.modules.pm3_strategy_engine.capabilities import PM3_STRATEGY_ENGINE_METADATA
from botmoduleproject1.modules.pm3_strategy_engine.config.schema import (
    Pm3StrategyEngineConfig,
    config_from_settings,
)
from botmoduleproject1.modules.pm3_strategy_engine.diagnostics.health import health_checks as se_health
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.adapters.event_publisher import (
    InMemoryEventPublisher,
)
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.adapters.pm2_context_adapter import (
    PM2ContextAdapter,
)
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.repositories.in_memory_bindings import (
    InMemoryBindingRepository,
)
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.repositories.in_memory_profiles import (
    InMemoryDraftRepository,
    InMemoryProfileRepository,
    InMemoryVersionRepository,
)
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.repositories.in_memory_trackers import (
    InMemoryTrackerRepository,
)
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.seed import seed_catalog
from botmoduleproject1.modules.pm3_strategy_engine.manifest import module_manifest
from botmoduleproject1.modules.pm3_strategy_engine.pipelines.feedback_pipe import FeedbackPipe
from botmoduleproject1.modules.pm3_strategy_engine.pipelines.global_system_pipe import GlobalSystemPipe
from botmoduleproject1.modules.pm3_strategy_engine.pipelines.symbol_pipe import SymbolPipe
from botmoduleproject1.modules.pm3_strategy_engine.templates.registry import TemplateRegistry


class PM3StrategyEngineModule:
    """Registered as pm3_strategy_engine. Produces TradeIntent | NoTradeDecision only."""

    def __init__(
        self,
        config: Pm3StrategyEngineConfig,
        clock: Any,
        *,
        feature_enabled: bool = True,
    ) -> None:
        self.config = config
        self.clock = clock
        self.feature_enabled = feature_enabled
        self.profiles = InMemoryProfileRepository()
        self.versions = InMemoryVersionRepository()
        self.drafts = InMemoryDraftRepository()
        self.bindings = InMemoryBindingRepository()
        self.trackers_repo = InMemoryTrackerRepository()
        self.publisher = InMemoryEventPublisher()
        seed_catalog(
            as_of=clock.now(),
            universe=config.universe,
            profiles=self.profiles,
            versions=self.versions,
            bindings=self.bindings,
        )
        self.templates = TemplateRegistry(enabled=config.enabled_templates)
        self.adapter = PM2ContextAdapter()
        self.calibration = CalibrationService(config.calibration_policy)
        self.consensus = ConsensusService(config.weights, config.thresholds)
        self.intents = IntentService(config.signal_expiry_hours)
        self.global_pipe = GlobalSystemPipe()
        self.profile_service = ProfileService(self.profiles, self.versions)
        self.draft_service = DraftService(self.versions, self.drafts, self.profiles, self.publisher)
        self.activation = ActivationService(self.profiles, self.versions, self.drafts, self.publisher)
        self.binding_service = SymbolBindingService(
            self.bindings, self.profiles, self.versions, self.publisher, config.max_active_branches
        )
        self.rollback = RollbackService(self.bindings, self.versions, self.publisher)
        self.trackers = TrackerService(self.trackers_repo)
        self.health_svc = HealthService()
        self.feedback = FeedbackPipe(self.trackers, self.health_svc)
        self.control = StrategyControlBridgeService(
            profiles=self.profile_service,
            bindings=self.binding_service,
            drafts=self.draft_service,
            activation=self.activation,
            rollback=self.rollback,
            trackers=self.trackers,
            health=self.health_svc,
        )
        self.handoff = PM2HandoffService()
        self._seen: dict[str, str] = {}
        self._last_signal: dict[str, SignalEvent] = {}
        self.symbol_pipe = SymbolPipe(
            config=config,
            templates=self.templates,
            bindings=self.bindings,
            profiles=self.profiles,
            versions=self.versions,
            adapter=self.adapter,
            calibration=self.calibration,
            consensus=self.consensus,
            intents=self.intents,
            global_pipe=self.global_pipe,
            feature_enabled=feature_enabled,
            seen_keys=self._seen,
        )

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM3StrategyEngineModule:
        flag = bool(getattr(settings, "feature_flags").strategy_engine)
        return cls(config_from_settings(settings), clock, feature_enabled=flag)

    def metadata(self) -> ModuleMetadata:
        return PM3_STRATEGY_ENGINE_METADATA

    def manifest(self) -> dict:
        return module_manifest()

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return se_health(kind, feature_enabled=self.feature_enabled)

    def latest_signal(self, symbol: str) -> SignalEvent | None:
        return self._last_signal.get(symbol)

    def evaluate_candidate(self, candidate: RankedCandidate) -> TradeIntent | NoTradeDecision:
        result = self.symbol_pipe.evaluate(candidate)
        if isinstance(result, TradeIntent):
            lead = result.profile_id or "unknown"
            ver = result.version_id or "unknown"
            self.trackers.note_intent(lead, ver, candidate.as_of)
            self._last_signal[candidate.symbol] = SignalEvent(
                correlation_id=result.correlation_id,
                causation_id=result.event_id,
                occurred_at=result.occurred_at,
                symbol=result.symbol,
                direction=result.direction,
                confluence=ConfluenceScore(value=result.consensus_score),
                producer="pm3_strategy_engine",
            )
        return result

    def evaluate_publication(
        self, bundle: PublicationBundle
    ) -> tuple[TradeIntent | NoTradeDecision, ...]:
        out: list[TradeIntent | NoTradeDecision] = []
        for candidate in self.handoff.candidates(bundle):
            out.append(self.evaluate_candidate(candidate))
        return tuple(out)

    def ingest_feedback(self, event: StrategyFeedbackEvent):
        return self.feedback.ingest(event)

    def run_backtest_hook(self) -> dict[str, str]:
        return {"status": "not_implemented", "note": "hook only; no backtest engine"}
