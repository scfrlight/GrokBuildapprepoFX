"""PM3-Strategy Engine template behaviour."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.adapters.pm2_context_adapter import (
    PM2ContextAdapter,
)
from botmoduleproject1.modules.pm3_strategy_engine.templates.liquidity_sweep_reversal import (
    LiquiditySweepReversalTemplate,
)
from botmoduleproject1.modules.pm3_strategy_engine.templates.mean_reversion import MeanReversionTemplate
from botmoduleproject1.modules.pm3_strategy_engine.templates.orb_session_breakout import (
    OrbSessionBreakoutTemplate,
)
from botmoduleproject1.modules.pm3_strategy_engine.templates.registry import TemplateRegistry
from botmoduleproject1.modules.pm3_strategy_engine.templates.trend_pullback import TrendPullbackTemplate
from botmoduleproject1.modules.pm3_strategy_engine.templates.volatility_squeeze_breakout import (
    VolatilitySqueezeBreakoutTemplate,
)
from tests.unit.pm3se_support import AS_OF, ranked_candidate

ADAPTER = PM2ContextAdapter()
PARAMS = {"historical_reliability": 0.55, "recent_live_health": 0.5}


def _ctx(**kwargs):
    cand = ranked_candidate(**kwargs)
    return ADAPTER.from_candidate(
        cand, profile_id="p", version_id="v", params=PARAMS, stale_ttl_hours=4
    )


def test_trend_pullback_votes_in_trending() -> None:
    vote = TrendPullbackTemplate().evaluate(_ctx(regime=RegimeType.TRENDING, side_bias="long"))
    assert vote.abstained is False
    assert vote.direction is Direction.BUY
    assert vote.strategy_template_type is StrategyTemplateType.TREND_PULLBACK


def test_orb_votes_in_session_breakout_context() -> None:
    vote = OrbSessionBreakoutTemplate().evaluate(
        _ctx(regime=RegimeType.TRANSITIONAL, side_bias="long", score=70)
    )
    assert vote.abstained is False
    assert vote.direction in {Direction.BUY, Direction.SELL}


def test_mean_reversion_abstains_in_trend() -> None:
    vote = MeanReversionTemplate().evaluate(_ctx(regime=RegimeType.TRENDING))
    assert vote.abstained is True
    assert vote.abstention_reason is VoteAbstentionReason.INCOMPATIBLE_REGIME


def test_mean_reversion_votes_in_range() -> None:
    vote = MeanReversionTemplate().evaluate(_ctx(regime=RegimeType.RANGING, side_bias="long"))
    assert vote.abstained is False


def test_second_phase_disabled_by_default() -> None:
    registry = TemplateRegistry()
    assert registry.is_enabled(StrategyTemplateType.TREND_PULLBACK)
    assert not registry.is_enabled(StrategyTemplateType.LIQUIDITY_SWEEP_REVERSAL)
    assert not registry.is_enabled(StrategyTemplateType.VOLATILITY_SQUEEZE_BREAKOUT)
    assert LiquiditySweepReversalTemplate.enabled_by_default is False
    assert VolatilitySqueezeBreakoutTemplate.enabled_by_default is False


def test_incompatible_regime_abstains() -> None:
    vote = TrendPullbackTemplate().evaluate(_ctx(regime=RegimeType.UNTRADEABLE))
    assert vote.abstained is True
    assert vote.abstention_reason is VoteAbstentionReason.INCOMPATIBLE_REGIME


def test_stale_and_malformed_no_vote() -> None:
    stale = TrendPullbackTemplate().evaluate(_ctx(quality=DataQualityStatus.STALE))
    bad = TrendPullbackTemplate().evaluate(_ctx(quality=DataQualityStatus.MALFORMED))
    assert stale.abstained and stale.abstention_reason is VoteAbstentionReason.STALE_CONTEXT
    assert bad.abstained and bad.abstention_reason is VoteAbstentionReason.MALFORMED_CONTEXT
