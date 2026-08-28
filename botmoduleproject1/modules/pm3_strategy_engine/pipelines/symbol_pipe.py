"""Per-symbol orchestration: PM2 candidate → votes → consensus → intent/no-trade."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, QualificationStateName, RankedCandidate
from botmoduleproject1.contracts.v1.strategy import NoTradeDecision, TradeIntent
from botmoduleproject1.contracts.v1.strategy_engine import StrategyVote, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.application.calibration_service import CalibrationService
from botmoduleproject1.modules.pm3_strategy_engine.application.consensus_service import ConsensusService
from botmoduleproject1.modules.pm3_strategy_engine.application.intent_service import IntentService
from botmoduleproject1.modules.pm3_strategy_engine.config.schema import Pm3StrategyEngineConfig
from botmoduleproject1.modules.pm3_strategy_engine.domain.factories import abstain_vote, no_trade
from botmoduleproject1.modules.pm3_strategy_engine.domain.policies import may_vote
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.adapters.pm2_context_adapter import (
    PM2ContextAdapter,
)
from botmoduleproject1.modules.pm3_strategy_engine.pipelines.global_system_pipe import GlobalSystemPipe
from botmoduleproject1.modules.pm3_strategy_engine.templates.registry import TemplateRegistry


class SymbolPipe:
    def __init__(
        self,
        *,
        config: Pm3StrategyEngineConfig,
        templates: TemplateRegistry,
        bindings,
        profiles,
        versions,
        adapter: PM2ContextAdapter,
        calibration: CalibrationService,
        consensus: ConsensusService,
        intents: IntentService,
        global_pipe: GlobalSystemPipe,
        feature_enabled: bool,
        seen_keys: dict[str, str] | None = None,
    ) -> None:
        self.config = config
        self.templates = templates
        self.bindings = bindings
        self.profiles = profiles
        self.versions = versions
        self.adapter = adapter
        self.calibration = calibration
        self.consensus = consensus
        self.intents = intents
        self.global_pipe = global_pipe
        self.feature_enabled = feature_enabled
        self.seen_keys = seen_keys if seen_keys is not None else {}
        self.last_votes: tuple[StrategyVote, ...] = ()

    def evaluate(self, candidate: RankedCandidate) -> TradeIntent | NoTradeDecision:
        as_of = candidate.as_of
        symbol = candidate.symbol
        corr = candidate.correlation_id

        if not self.feature_enabled:
            return no_trade(symbol, as_of, "feature_flag_off", correlation_id=corr)

        if not self.global_pipe.evaluation_permitted():
            return no_trade(symbol, as_of, "system_flag_disabled", correlation_id=corr)

        quality = candidate.context.data_quality
        if quality is DataQualityStatus.STALE:
            return no_trade(symbol, as_of, "stale_pm2_context", correlation_id=corr)
        if quality in {DataQualityStatus.MALFORMED, DataQualityStatus.INCOMPLETE}:
            return no_trade(symbol, as_of, "bad_data_quality", correlation_id=corr)
        if candidate.state.state is QualificationStateName.STALE:
            return no_trade(symbol, as_of, "stale_qualification", correlation_id=corr)
        if candidate.context.as_of > candidate.as_of:
            return no_trade(symbol, as_of, "lookahead", correlation_id=corr)

        if self.config.require_handoff_eligibility and not candidate.handoff_eligibility:
            return no_trade(
                symbol,
                as_of,
                "handoff_ineligible",
                correlation_id=corr,
                diagnostics={"observe_only": True, "shadow_eval": True},
            )

        active = [b for b in self.bindings.list_for_symbol(symbol) if b.active]
        if len(active) > self.config.max_active_branches:
            return no_trade(symbol, as_of, "max_branches_exceeded", correlation_id=corr)

        votes: list[StrategyVote] = []
        for binding in active:
            profile = self.profiles.get(binding.profile_id)
            version = self.versions.get(binding.version_id)
            if profile is None or version is None:
                continue
            if not may_vote(profile.status) or not may_vote(version.status):
                votes.append(
                    abstain_vote(
                        template=binding.template_type,
                        profile_id=binding.profile_id,
                        version_id=binding.version_id,
                        symbol=symbol,
                        as_of=as_of,
                        reason=VoteAbstentionReason.DISABLED_PROFILE,
                        correlation_id=corr,
                    )
                )
                continue
            if not self.templates.is_enabled(binding.template_type):
                votes.append(
                    abstain_vote(
                        template=binding.template_type,
                        profile_id=binding.profile_id,
                        version_id=binding.version_id,
                        symbol=symbol,
                        as_of=as_of,
                        reason=VoteAbstentionReason.DISABLED_TEMPLATE,
                        correlation_id=corr,
                    )
                )
                continue
            ctx = self.adapter.from_candidate(
                candidate,
                profile_id=binding.profile_id,
                version_id=binding.version_id,
                params=dict(version.parameters),
                stale_ttl_hours=self.config.stale_ttl_hours,
                flags=self.global_pipe.flags,
            )
            raw_vote = self.templates.get(binding.template_type).evaluate(ctx)
            votes.append(self.calibration.apply(raw_vote))

        self.last_votes = tuple(votes)
        consensus = self.consensus.decide(tuple(votes), symbol=symbol, as_of=as_of)
        lead_profile = active[0].profile_id if active else None
        lead_version = active[0].version_id if active else None
        artifact = self.intents.from_consensus(
            consensus, candidate, profile_id=lead_profile, version_id=lead_version
        )
        if isinstance(artifact, TradeIntent):
            if artifact.idempotency_key in self.seen_keys:
                return no_trade(
                    symbol,
                    as_of,
                    "duplicate_intent",
                    correlation_id=corr,
                    diagnostics={"idempotency_key": artifact.idempotency_key},
                )
            self.seen_keys[artifact.idempotency_key] = "issued"
        return artifact
