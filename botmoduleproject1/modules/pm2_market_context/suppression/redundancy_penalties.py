"""Penalize shared-currency overlap. Does not size or route."""

from __future__ import annotations

from botmoduleproject1.modules.pm2_market_context.engines.correlation_engine import shared_currency
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


def overlap_penalty(symbol: str, kept: tuple[str, ...]) -> float:
    hits = sum(1 for other in kept if other != symbol and shared_currency(symbol, other))
    return clamp(hits * 6.0, 0.0, 18.0)
