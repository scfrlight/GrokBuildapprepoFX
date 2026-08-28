"""Deterministic regime baseline. Not bullish/bearish."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot


def classify_regime(snapshot: FeatureSnapshot) -> tuple[RegimeType, float]:
    atr_pct = snapshot.atr_pct
    trend = snapshot.sma_fast - snapshot.sma_slow
    trend_pct = abs(trend) / snapshot.close if snapshot.close else 0.0
    mom = abs(snapshot.roc_n)

    if snapshot.bars < 16:
        return RegimeType.UNTRADEABLE, 0.2
    if atr_pct >= 0.012:
        return RegimeType.VOLATILE, min(0.95, 0.55 + atr_pct * 20)
    if atr_pct <= 0.0018:
        return RegimeType.COMPRESSION, min(0.9, 0.5 + (0.002 - atr_pct) * 80)
    if trend_pct >= 0.0025 and mom >= 0.001:
        return RegimeType.TRENDING, min(0.92, 0.55 + trend_pct * 80)
    if trend_pct < 0.0008 and mom < 0.0015:
        return RegimeType.RANGING, min(0.88, 0.5 + (0.001 - trend_pct) * 100)
    if mom > 0.004 and trend_pct < 0.001:
        return RegimeType.TRANSITIONAL, 0.45
    return RegimeType.TRANSITIONAL, 0.4
