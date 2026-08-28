"""Replaceable template registry. No code edit required to disable a family."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType
from botmoduleproject1.modules.pm3_strategy_engine.templates.base import BaseTemplate
from botmoduleproject1.modules.pm3_strategy_engine.templates.liquidity_sweep_reversal import (
    LiquiditySweepReversalTemplate,
)
from botmoduleproject1.modules.pm3_strategy_engine.templates.mean_reversion import MeanReversionTemplate
from botmoduleproject1.modules.pm3_strategy_engine.templates.orb_session_breakout import (
    OrbSessionBreakoutTemplate,
)
from botmoduleproject1.modules.pm3_strategy_engine.templates.trend_pullback import TrendPullbackTemplate
from botmoduleproject1.modules.pm3_strategy_engine.templates.volatility_squeeze_breakout import (
    VolatilitySqueezeBreakoutTemplate,
)

_DEFAULTS: tuple[type[BaseTemplate], ...] = (
    TrendPullbackTemplate,
    OrbSessionBreakoutTemplate,
    MeanReversionTemplate,
    LiquiditySweepReversalTemplate,
    VolatilitySqueezeBreakoutTemplate,
)


class TemplateRegistry:
    def __init__(self, enabled: tuple[str, ...] | None = None) -> None:
        self._by_type: dict[StrategyTemplateType, BaseTemplate] = {
            cls.template_type: cls() for cls in _DEFAULTS
        }
        self._enabled = set(enabled) if enabled is not None else {
            t.template_type.value for t in self._by_type.values() if t.enabled_by_default
        }

    def get(self, template_type: StrategyTemplateType) -> BaseTemplate:
        return self._by_type[template_type]

    def is_enabled(self, template_type: StrategyTemplateType) -> bool:
        return template_type.value in self._enabled

    def all_types(self) -> tuple[StrategyTemplateType, ...]:
        return tuple(self._by_type)

    def enabled_types(self) -> tuple[StrategyTemplateType, ...]:
        return tuple(t for t in self._by_type if t.value in self._enabled)
