"""Trend Pullback / Continuation — first phase, enabled."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.domain.factories import abstain_vote
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext
from botmoduleproject1.modules.pm3_strategy_engine.templates.base import BaseTemplate, unit


class TrendPullbackTemplate(BaseTemplate):
    template_type = StrategyTemplateType.TREND_PULLBACK
    enabled_by_default = True
    supported_regimes = frozenset({RegimeType.TRENDING})

    def evaluate(self, context: EvaluationContext) -> StrategyVote:
        gated = self._gate(context)
        if gated is not None:
            return gated
        long_s = context.features.long_score
        short_s = context.features.short_score
        if context.side_bias == "long" or long_s > short_s + 5:
            direction = Direction.BUY
            raw = 0.55 + 0.35 * unit(long_s)
        elif context.side_bias == "short" or short_s > long_s + 5:
            direction = Direction.SELL
            raw = 0.55 + 0.35 * unit(short_s)
        else:
            return abstain_vote(
                template=self.template_type,
                profile_id=context.profile_id,
                version_id=context.version_id,
                symbol=context.symbol,
                as_of=context.as_of,
                reason=VoteAbstentionReason.INSUFFICIENT_EVIDENCE,
                correlation_id=context.candidate.correlation_id,
            )
        return self._vote(
            context,
            direction,
            raw,
            regime_fit=0.85,
            setup_quality=max(unit(context.features.structure), unit(context.features.confluence)),
            friction_fit=0.65,
        )
