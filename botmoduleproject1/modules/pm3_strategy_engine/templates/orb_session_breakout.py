"""ORB / Session Breakout — first phase, enabled."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.domain.factories import abstain_vote
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext
from botmoduleproject1.modules.pm3_strategy_engine.templates.base import BaseTemplate, unit


class OrbSessionBreakoutTemplate(BaseTemplate):
    template_type = StrategyTemplateType.ORB_SESSION_BREAKOUT
    enabled_by_default = True
    supported_regimes = frozenset(
        {RegimeType.TRANSITIONAL, RegimeType.COMPRESSION, RegimeType.TRENDING}
    )

    def evaluate(self, context: EvaluationContext) -> StrategyVote:
        gated = self._gate(context)
        if gated is not None:
            return gated
        if context.session_quality < 0.4:
            return abstain_vote(
                template=self.template_type,
                profile_id=context.profile_id,
                version_id=context.version_id,
                symbol=context.symbol,
                as_of=context.as_of,
                reason=VoteAbstentionReason.INSUFFICIENT_EVIDENCE,
                correlation_id=context.candidate.correlation_id,
                diagnostics={"session_quality": context.session_quality},
            )
        momentum = context.features.momentum
        if context.side_bias == "short" or context.features.short_score > context.features.long_score + 8:
            direction = Direction.SELL
        else:
            direction = Direction.BUY
        raw = 0.52 + 0.30 * unit(momentum) + 0.10 * context.session_quality
        return self._vote(
            context,
            direction,
            min(0.95, raw),
            regime_fit=0.70 if context.regime is not RegimeType.TRENDING else 0.60,
            setup_quality=max(unit(momentum), context.session_quality),
            friction_fit=0.55,
        )
