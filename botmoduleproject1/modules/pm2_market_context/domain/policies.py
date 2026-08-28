"""Feature-family governance: one family, one cap, no fake confluence."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import FeatureFamily

FAMILY_CAPS: dict[FeatureFamily, float] = {
    FeatureFamily.REGIME: 20.0,
    FeatureFamily.DIRECTIONAL_BIAS: 20.0,
    FeatureFamily.STRUCTURE: 15.0,
    FeatureFamily.MOMENTUM: 15.0,
    FeatureFamily.VOLATILITY: 10.0,
    FeatureFamily.SESSION_LIQUIDITY: 10.0,
    FeatureFamily.CORRELATION: 10.0,
    FeatureFamily.MACRO: 5.0,
}

DEFAULT_WEIGHTS: dict[FeatureFamily, float] = {
    FeatureFamily.REGIME: 1.0,
    FeatureFamily.DIRECTIONAL_BIAS: 1.0,
    FeatureFamily.STRUCTURE: 0.9,
    FeatureFamily.MOMENTUM: 0.85,
    FeatureFamily.VOLATILITY: 0.7,
    FeatureFamily.SESSION_LIQUIDITY: 0.6,
    FeatureFamily.CORRELATION: 0.5,
    FeatureFamily.MACRO: 0.0,
}

REQUIRED_FAMILIES = (
    FeatureFamily.REGIME,
    FeatureFamily.DIRECTIONAL_BIAS,
    FeatureFamily.STRUCTURE,
    FeatureFamily.MOMENTUM,
    FeatureFamily.VOLATILITY,
    FeatureFamily.SESSION_LIQUIDITY,
    FeatureFamily.CORRELATION,
)


def cap_contribution(family: FeatureFamily, raw: float) -> float:
    cap = FAMILY_CAPS[family]
    value = max(0.0, min(float(raw), cap))
    return value
