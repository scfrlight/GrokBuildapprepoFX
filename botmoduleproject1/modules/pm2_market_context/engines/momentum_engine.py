"""Momentum pressure, slope, stability."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


class MomentumResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    long_momentum: float = Field(ge=0.0, le=100.0)
    short_momentum: float = Field(ge=0.0, le=100.0)
    stability: float = Field(ge=0.0, le=1.0)
    strengthening: bool


def evaluate_momentum(snapshot: FeatureSnapshot) -> MomentumResult:
    rate = snapshot.roc_n
    long_m = clamp(50 + rate * 4000)
    short_m = clamp(50 - rate * 4000)
    strengthening = abs(rate) > 0.001
    stability = clamp(1.0 - min(abs(rate) * 80, 0.8), 0.0, 1.0)
    return MomentumResult(
        long_momentum=long_m,
        short_momentum=short_m,
        stability=stability,
        strengthening=strengthening,
    )
