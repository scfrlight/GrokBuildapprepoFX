"""Weighted confluence with family caps, penalties, vetoes. Long and short split."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import (
    CandidateScoreCard,
    FeatureFamily,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config
from botmoduleproject1.modules.pm2_market_context.domain.policies import cap_contribution
from botmoduleproject1.modules.pm2_market_context.engines.bias_engine import BiasResult
from botmoduleproject1.modules.pm2_market_context.engines.momentum_engine import MomentumResult
from botmoduleproject1.modules.pm2_market_context.engines.session_liquidity_engine import SessionLiquidityResult
from botmoduleproject1.modules.pm2_market_context.engines.structure_engine import StructureResult
from botmoduleproject1.modules.pm2_market_context.engines.volatility_engine import VolatilityResult
from botmoduleproject1.modules.pm2_market_context.features.governance import redundancy_penalty
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp
from botmoduleproject1.modules.pm2_market_context.scoring.confidence import confidence_score
from botmoduleproject1.modules.pm2_market_context.scoring.penalties import (
    directional_conflict_penalty,
    untradeable_penalty,
)
from botmoduleproject1.modules.pm2_market_context.scoring.weights import family_weights


def score(
    *,
    config: Pm2Config,
    regime: RegimeType,
    regime_confidence: float,
    bias: BiasResult,
    structure: StructureResult,
    momentum: MomentumResult,
    volatility: VolatilityResult,
    session: SessionLiquidityResult,
    veto_list: tuple[str, ...],
    quality,
) -> CandidateScoreCard:
    weights = family_weights(config.weights)
    regime_s = clamp(regime_confidence * 100)
    contrib = {
        FeatureFamily.REGIME: cap_contribution(FeatureFamily.REGIME, regime_s * 0.2 * weights[FeatureFamily.REGIME]),
        FeatureFamily.DIRECTIONAL_BIAS: cap_contribution(
            FeatureFamily.DIRECTIONAL_BIAS, max(bias.long_bias_score, bias.short_bias_score) * 0.2 * weights[FeatureFamily.DIRECTIONAL_BIAS]
        ),
        FeatureFamily.STRUCTURE: cap_contribution(FeatureFamily.STRUCTURE, structure.quality * 0.15 * weights[FeatureFamily.STRUCTURE] / 0.9),
        FeatureFamily.MOMENTUM: cap_contribution(
            FeatureFamily.MOMENTUM, max(momentum.long_momentum, momentum.short_momentum) * 0.15 * weights[FeatureFamily.MOMENTUM]
        ),
        FeatureFamily.VOLATILITY: cap_contribution(FeatureFamily.VOLATILITY, volatility.score * 0.10 * weights[FeatureFamily.VOLATILITY]),
        FeatureFamily.SESSION_LIQUIDITY: cap_contribution(
            FeatureFamily.SESSION_LIQUIDITY, session.session_score * 0.10 * weights[FeatureFamily.SESSION_LIQUIDITY]
        ),
        FeatureFamily.CORRELATION: 0.0,
        FeatureFamily.MACRO: 0.0,
    }
    red = redundancy_penalty(contrib)
    conflict = directional_conflict_penalty(bias)
    untr = untradeable_penalty(regime)
    raw = sum(contrib.values())
    final = clamp(raw - red - conflict - untr)
    if veto_list:
        final = min(final, 39.0)
    long_s = clamp((bias.long_bias_score + momentum.long_momentum) / 2)
    short_s = clamp((bias.short_bias_score + momentum.short_momentum) / 2)
    conf = confidence_score(
        regime_confidence=regime_confidence,
        momentum_stability=momentum.stability,
        quality=quality,
        veto_count=len(veto_list),
    )
    components = {k.value: v for k, v in contrib.items()}
    components["redundancy_penalty"] = red
    components["conflict_penalty"] = conflict
    return CandidateScoreCard(
        long_score=long_s,
        short_score=short_s,
        final_confluence_score=final,
        directional_edge_gap=abs(long_s - short_s),
        regime_score=regime_s,
        structure_score=structure.quality,
        momentum_score=max(momentum.long_momentum, momentum.short_momentum),
        volatility_score=volatility.score,
        session_score=session.session_score,
        liquidity_score=session.liquidity_score,
        correlation_penalty=0.0,
        feature_redundancy_penalty=red,
        confidence_score=conf,
        quality_tier=quality_tier_for(final),
        components=components,
        vetoes=veto_list,
    )
