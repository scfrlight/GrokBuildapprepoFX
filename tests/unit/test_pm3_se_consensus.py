"""PM3-Strategy Engine consensus + calibration."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy import ConsensusDecision, Direction, EntryType
from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType, StrategyVote
from botmoduleproject1.modules.pm3_strategy_engine.consensus.calibration import (
    RELIABILITY_TABLE,
    ReliabilityTablePolicy,
    _interp,
)
from botmoduleproject1.modules.pm3_strategy_engine.consensus.thresholds import vote_weight
from botmoduleproject1.modules.pm3_strategy_engine.consensus.weighted_ensemble import WeightedEnsembleConsensus
from botmoduleproject1.modules.pm3_strategy_engine.config.schema import ConsensusWeights
from tests.unit.pm3se_support import AS_OF


def _vote(*, direction: Direction, p: float, h=0.8, r=0.8, q=0.8, f=0.6, live=0.5, abstain=False) -> StrategyVote:
    return StrategyVote(
        occurred_at=AS_OF,
        strategy_template_type=StrategyTemplateType.TREND_PULLBACK,
        profile_id="p",
        version_id="v",
        symbol="EURUSD",
        direction=direction,
        raw_probability=p,
        calibrated_probability=p,
        setup_quality=q,
        regime_fit=r,
        friction_fit=f,
        historical_reliability=h,
        recent_live_health=live,
        entry_type=EntryType.LIMIT,
        abstained=abstain,
    )


def test_base_weight_formula() -> None:
    w = ConsensusWeights()
    value = vote_weight(1, 1, 1, 1, 1, w)
    assert abs(value - 1.0) < 1e-9
    value = vote_weight(0.5, 0.5, 0.5, 0.5, 0.5, w)
    assert abs(value - 0.5) < 1e-9
    expected = 0.35 * 0.8 + 0.25 * 0.7 + 0.20 * 0.6 + 0.10 * 0.5 + 0.10 * 0.4
    assert abs(vote_weight(0.8, 0.7, 0.6, 0.5, 0.4, w) - expected) < 1e-9


def test_go_long_and_go_short() -> None:
    engine = WeightedEnsembleConsensus()
    long = engine.decide((_vote(direction=Direction.BUY, p=0.8),), symbol="EURUSD", as_of=AS_OF)
    assert long.decision is ConsensusDecision.GO_LONG
    assert long.p_long >= 0.55
    short = engine.decide((_vote(direction=Direction.SELL, p=0.8),), symbol="EURUSD", as_of=AS_OF)
    assert short.decision is ConsensusDecision.GO_SHORT


def test_wait_when_insufficient() -> None:
    engine = WeightedEnsembleConsensus()
    result = engine.decide((), symbol="EURUSD", as_of=AS_OF)
    assert result.decision is ConsensusDecision.WAIT


def test_no_trade_on_conflict() -> None:
    engine = WeightedEnsembleConsensus()
    result = engine.decide(
        (
            _vote(direction=Direction.BUY, p=0.7, h=0.9, r=0.9, q=0.9),
            _vote(direction=Direction.SELL, p=0.7, h=0.9, r=0.9, q=0.9),
        ),
        symbol="EURUSD",
        as_of=AS_OF,
    )
    assert result.decision is ConsensusDecision.NO_TRADE
    assert result.conflict_score >= 0.35


def test_deterministic() -> None:
    engine = WeightedEnsembleConsensus()
    votes = (_vote(direction=Direction.BUY, p=0.72), _vote(direction=Direction.BUY, p=0.66))
    a = engine.decide(votes, symbol="EURUSD", as_of=AS_OF)
    b = engine.decide(votes, symbol="EURUSD", as_of=AS_OF)
    assert a.decision is b.decision
    assert a.p_long == b.p_long
    assert a.p_short == b.p_short


def test_degraded_abstain_dropped() -> None:
    engine = WeightedEnsembleConsensus()
    result = engine.decide(
        (
            _vote(direction=Direction.BUY, p=0.9, abstain=True),
            _vote(direction=Direction.BUY, p=0.8),
        ),
        symbol="EURUSD",
        as_of=AS_OF,
    )
    assert len(result.dropped_votes) == 1
    assert len(result.selected_votes) == 1
    assert result.decision is ConsensusDecision.GO_LONG


def test_calibration_changes_probability() -> None:
    raw = _vote(direction=Direction.BUY, p=0.80)
    cal = ReliabilityTablePolicy().calibrate(raw)
    assert cal.raw_probability == 0.80
    assert cal.calibrated_probability != cal.raw_probability
    assert cal.calibrated_probability == _interp(0.80, RELIABILITY_TABLE)
    assert cal.calibration_version == "reliability_table.v1"
    assert cal.calibration_fallback is False


def test_long_short_separated() -> None:
    engine = WeightedEnsembleConsensus()
    result = engine.decide(
        (_vote(direction=Direction.BUY, p=0.9), _vote(direction=Direction.SELL, p=0.2, h=0.2, r=0.2, q=0.2)),
        symbol="EURUSD",
        as_of=AS_OF,
    )
    assert result.p_long > 0
    assert result.p_short > 0
    assert result.p_long != result.p_short
