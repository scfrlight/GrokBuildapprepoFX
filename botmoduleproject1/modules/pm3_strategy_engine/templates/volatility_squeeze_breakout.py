"""Volatility Squeeze Breakout — second phase, disabled by default."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import EvaluationContext
from botmoduleproject1.modules.pm3_strategy_engine.templates.base import BaseTemplate, unit


class VolatilitySqueezeBreakoutTemplate(BaseTemplate):
    template_type = StrategyTemplateType.VOLATILITY_SQUEEZE_BREAKOUT
    enabled_by_default = False
    supported_regimes = frozenset({RegimeType.COMPRESSION, RegimeType.TRANSITIONAL})

    def evaluate(self, context: EvaluationContext) -> StrategyVote:
        gated = self._gate(context)
        if gated is not None:
            return gated
        direction = Direction.SELL if context.side_bias == "short" else Direction.BUY
        raw = 0.50 + 0.25 * unit(context.features.momentum)
        return self._vote(
            context,
            direction,
            raw,
            regime_fit=0.72,
            setup_quality=unit(100.0 - context.features.volatility) if context.features.volatility else 0.5,
            friction_fit=0.50,
        )
