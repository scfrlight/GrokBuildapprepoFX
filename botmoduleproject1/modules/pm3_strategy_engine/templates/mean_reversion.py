"""Mean Reversion — first phase, enabled. Abstains in trend."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext
from botmoduleproject1.modules.pm3_strategy_engine.templates.base import BaseTemplate, unit


class MeanReversionTemplate(BaseTemplate):
    template_type = StrategyTemplateType.MEAN_REVERSION
    enabled_by_default = True
    supported_regimes = frozenset({RegimeType.RANGING})

    def evaluate(self, context: EvaluationContext) -> StrategyVote:
        gated = self._gate(context)
        if gated is not None:
            return gated
        # Fade the stretched side.
        if context.features.long_score >= context.features.short_score:
            direction = Direction.SELL
            raw = 0.50 + 0.30 * unit(context.features.long_score)
        else:
            direction = Direction.BUY
            raw = 0.50 + 0.30 * unit(context.features.short_score)
        return self._vote(
            context,
            direction,
            raw,
            regime_fit=0.80,
            setup_quality=unit(context.features.confluence),
            friction_fit=0.60,
        )
