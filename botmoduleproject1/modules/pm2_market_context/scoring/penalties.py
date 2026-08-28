"""Penalties: conflict, redundancy, untradeable regime."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.modules.pm2_market_context.engines.bias_engine import BiasResult


def directional_conflict_penalty(bias: BiasResult) -> float:
    if abs(bias.net_bias_score) < 8:
        return 12.0
    return 0.0


def untradeable_penalty(regime: RegimeType) -> float:
    if regime is RegimeType.UNTRADEABLE:
        return 40.0
    if regime is RegimeType.TRANSITIONAL:
        return 10.0
    return 0.0
