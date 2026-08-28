from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote
from botmoduleproject1.modules.pm3_strategy_engine.consensus.calibration import (
    ConservativeFallbackPolicy,
    ReliabilityTablePolicy,
)
from tests.unit.pm3se_support import AS_OF


def test_out_of_range_is_clipped() -> None:
    vote = StrategyVote(
        occurred_at=AS_OF,
        strategy_template_type=StrategyTemplateType.TREND_PULLBACK,
        profile_id="p",
        version_id="v",
        symbol="EURUSD",
        direction=Direction.BUY,
        raw_probability=1.0,
        calibrated_probability=1.0,
        setup_quality=1.0,
        regime_fit=1.0,
        friction_fit=1.0,
        historical_reliability=1.0,
        recent_live_health=1.0,
        entry_type=EntryType.LIMIT,
    )
    out = ReliabilityTablePolicy().calibrate(vote)
    assert 0.0 <= out.calibrated_probability <= 1.0


def test_fallback_is_marked() -> None:
    vote = StrategyVote(
        occurred_at=AS_OF,
        strategy_template_type=StrategyTemplateType.TREND_PULLBACK,
        profile_id="p",
        version_id="v",
        symbol="EURUSD",
        direction=Direction.BUY,
        raw_probability=0.9,
        calibrated_probability=0.9,
        setup_quality=0.5,
        regime_fit=0.5,
        friction_fit=0.5,
        historical_reliability=0.5,
        recent_live_health=0.5,
        entry_type=EntryType.LIMIT,
    )
    out = ConservativeFallbackPolicy().calibrate(vote)
    assert out.calibration_fallback is True
    assert out.diagnostics.get("calibration") == "fallback"
    assert out.calibrated_probability != out.raw_probability
