"""Volatility phase — not raw ATR."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from botmoduleproject1.modules.pm2_market_context.domain.enums import VolatilityPhase
from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


class VolatilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    phase: VolatilityPhase
    tradability: float
    score: float


def evaluate_volatility(snapshot: FeatureSnapshot) -> VolatilityResult:
    pct = snapshot.atr_pct
    if pct >= 0.015:
        phase = VolatilityPhase.SHOCK
        tradability = 25.0
    elif pct >= 0.008:
        phase = VolatilityPhase.EXPANSION
        tradability = 55.0
    elif pct <= 0.0007:
        phase = VolatilityPhase.DEAD
        tradability = 15.0
    elif pct <= 0.0015:
        phase = VolatilityPhase.COMPRESSION
        tradability = 40.0
    else:
        phase = VolatilityPhase.EXHAUSTION if abs(snapshot.roc_n) < 0.0004 else VolatilityPhase.EXPANSION
        tradability = 60.0
    score = clamp(tradability + (0.004 - abs(pct - 0.004)) * 2000)
    return VolatilityResult(phase=phase, tradability=clamp(tradability), score=score)
