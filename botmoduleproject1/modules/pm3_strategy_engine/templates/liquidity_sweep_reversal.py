"""Liquidity Sweep Reversal — second phase, disabled by default."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.domain.factories import abstain_vote
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext
from botmoduleproject1.modules.pm3_strategy_engine.templates.base import BaseTemplate, unit


class LiquiditySweepReversalTemplate(BaseTemplate):
    template_type = StrategyTemplateType.LIQUIDITY_SWEEP_REVERSAL
    enabled_by_default = False
    supported_regimes = frozenset({RegimeType.RANGING})

    def evaluate(self, context: EvaluationContext) -> StrategyVote:
        gated = self._gate(context)
        if gated is not None:
            return gated
        if context.features.structure < 40:
            return abstain_vote(
                template=self.template_type,
                profile_id=context.profile_id,
                version_id=context.version_id,
                symbol=context.symbol,
                as_of=context.as_of,
                reason=VoteAbstentionReason.INSUFFICIENT_EVIDENCE,
                correlation_id=context.candidate.correlation_id,
            )
        direction = Direction.BUY if context.side_bias == "short" else Direction.SELL
        return self._vote(
            context,
            direction,
            0.48 + 0.20 * unit(context.features.structure),
            regime_fit=0.55,
            setup_quality=unit(context.features.structure),
            friction_fit=0.45,
        )
