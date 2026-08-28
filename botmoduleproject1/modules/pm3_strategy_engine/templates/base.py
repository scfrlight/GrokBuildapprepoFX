"""Shared template helpers. Templates consume EvaluationContext only."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.domain.factories import abstain_vote, directional_vote
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext


def unit(score_0_100: float) -> float:
    return min(1.0, max(0.0, score_0_100 / 100.0))


class BaseTemplate:
    template_type: StrategyTemplateType
    enabled_by_default: bool = True
    supported_regimes: frozenset[RegimeType] = frozenset()

    def _gate(self, ctx: EvaluationContext) -> StrategyVote | None:
        if ctx.lookahead:
            return abstain_vote(
                template=self.template_type,
                profile_id=ctx.profile_id,
                version_id=ctx.version_id,
                symbol=ctx.symbol,
                as_of=ctx.as_of,
                reason=VoteAbstentionReason.LOOKAHEAD,
                correlation_id=ctx.candidate.correlation_id,
            )
        if ctx.malformed:
            return abstain_vote(
                template=self.template_type,
                profile_id=ctx.profile_id,
                version_id=ctx.version_id,
                symbol=ctx.symbol,
                as_of=ctx.as_of,
                reason=VoteAbstentionReason.MALFORMED_CONTEXT,
                correlation_id=ctx.candidate.correlation_id,
            )
        if ctx.stale or ctx.data_quality in {DataQualityStatus.STALE, DataQualityStatus.INCOMPLETE}:
            return abstain_vote(
                template=self.template_type,
                profile_id=ctx.profile_id,
                version_id=ctx.version_id,
                symbol=ctx.symbol,
                as_of=ctx.as_of,
                reason=VoteAbstentionReason.STALE_CONTEXT,
                correlation_id=ctx.candidate.correlation_id,
            )
        if ctx.data_quality is DataQualityStatus.MALFORMED:
            return abstain_vote(
                template=self.template_type,
                profile_id=ctx.profile_id,
                version_id=ctx.version_id,
                symbol=ctx.symbol,
                as_of=ctx.as_of,
                reason=VoteAbstentionReason.DATA_QUALITY,
                correlation_id=ctx.candidate.correlation_id,
            )
        if ctx.regime not in self.supported_regimes:
            return abstain_vote(
                template=self.template_type,
                profile_id=ctx.profile_id,
                version_id=ctx.version_id,
                symbol=ctx.symbol,
                as_of=ctx.as_of,
                reason=VoteAbstentionReason.INCOMPATIBLE_REGIME,
                correlation_id=ctx.candidate.correlation_id,
                diagnostics={"regime": ctx.regime.value},
            )
        return None

    def _vote(
        self,
        ctx: EvaluationContext,
        direction: Direction,
        raw: float,
        *,
        regime_fit: float,
        setup_quality: float,
        friction_fit: float = 0.6,
    ) -> StrategyVote:
        hist = float(ctx.params.get("historical_reliability", 0.55))
        live = float(ctx.params.get("recent_live_health", 0.50))
        return directional_vote(
            template=self.template_type,
            profile_id=ctx.profile_id,
            version_id=ctx.version_id,
            symbol=ctx.symbol,
            as_of=ctx.as_of,
            direction=direction,
            raw=raw,
            setup_quality=setup_quality,
            regime_fit=regime_fit,
            friction_fit=friction_fit,
            historical_reliability=hist,
            recent_live_health=live,
            correlation_id=ctx.candidate.correlation_id,
            hints={"side_bias": ctx.side_bias, "regime": ctx.regime.value},
            diagnostics={"template": self.template_type.value, "confluence": ctx.features.confluence},
        )
