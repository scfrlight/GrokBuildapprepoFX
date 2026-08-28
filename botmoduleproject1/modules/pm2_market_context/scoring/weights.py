"""Score weights from config."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import FeatureFamily
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Weights


def family_weights(cfg: Pm2Weights) -> dict[FeatureFamily, float]:
    return {
        FeatureFamily.REGIME: cfg.regime,
        FeatureFamily.DIRECTIONAL_BIAS: cfg.directional_bias,
        FeatureFamily.STRUCTURE: cfg.structure,
        FeatureFamily.MOMENTUM: cfg.momentum,
        FeatureFamily.VOLATILITY: cfg.volatility,
        FeatureFamily.SESSION_LIQUIDITY: cfg.session_liquidity,
        FeatureFamily.CORRELATION: cfg.correlation,
        FeatureFamily.MACRO: cfg.macro,
    }
