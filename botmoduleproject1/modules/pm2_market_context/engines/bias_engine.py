"""Multi-timeframe directional bias. Weighted, not binary alignment."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


class BiasResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    long_bias_score: float = Field(ge=0.0, le=100.0)
    short_bias_score: float = Field(ge=0.0, le=100.0)
    net_bias_score: float


def evaluate_bias(snapshots: dict[str, FeatureSnapshot]) -> BiasResult:
    weights = {"M15": 0.2, "H1": 0.5, "H4": 0.3, "M5": 0.1, "M30": 0.15}
    long_acc = 0.0
    short_acc = 0.0
    wsum = 0.0
    for tf, snap in snapshots.items():
        w = weights.get(tf, 0.25)
        trend = snap.sma_fast - snap.sma_slow
        long_e = clamp(50 + trend / max(snap.atr, 1e-8) * 8)
        short_e = clamp(50 - trend / max(snap.atr, 1e-8) * 8)
        long_acc += long_e * w
        short_acc += short_e * w
        wsum += w
    if wsum == 0:
        return BiasResult(long_bias_score=50.0, short_bias_score=50.0, net_bias_score=0.0)
    long_s = long_acc / wsum
    short_s = short_acc / wsum
    return BiasResult(
        long_bias_score=long_s,
        short_bias_score=short_s,
        net_bias_score=long_s - short_s,
    )
