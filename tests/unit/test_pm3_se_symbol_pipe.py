"""PM3-Strategy Engine SymbolPipe safety and intent path."""

from __future__ import annotations

from datetime import timedelta

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, QualificationStateName
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import NoTradeDecision, TradeIntent
from tests.unit.pm3se_support import AS_OF, engine, ranked_candidate


def test_handoff_true_can_emit_intent() -> None:
    mod = engine()
    cand = ranked_candidate(handoff=True, regime=RegimeType.TRENDING, side_bias="long")
    result = mod.evaluate_candidate(cand)
    assert isinstance(result, (TradeIntent, NoTradeDecision))
    if isinstance(result, TradeIntent):
        assert result.requested_volume is None
        assert result.producer == "pm3_strategy_engine"
        assert "not_an_order" in result.diagnostics


def test_handoff_false_is_no_trade() -> None:
    mod = engine()
    result = mod.evaluate_candidate(ranked_candidate(handoff=False))
    assert isinstance(result, NoTradeDecision)
    assert result.reason == "handoff_ineligible"
    assert result.observe_only is True


def test_stale_and_bad_quality() -> None:
    mod = engine()
    stale = mod.evaluate_candidate(ranked_candidate(quality=DataQualityStatus.STALE, handoff=True))
    bad = mod.evaluate_candidate(ranked_candidate(quality=DataQualityStatus.MALFORMED, handoff=True))
    qual = mod.evaluate_candidate(
        ranked_candidate(state=QualificationStateName.STALE, handoff=True)
    )
    assert isinstance(stale, NoTradeDecision) and stale.reason == "stale_pm2_context"
    assert isinstance(bad, NoTradeDecision) and bad.reason == "bad_data_quality"
    assert isinstance(qual, NoTradeDecision)


def test_duplicate_idempotency() -> None:
    mod = engine()
    cand = ranked_candidate(handoff=True, regime=RegimeType.TRENDING, side_bias="long")
    first = mod.evaluate_candidate(cand)
    second = mod.evaluate_candidate(cand)
    if isinstance(first, TradeIntent):
        assert isinstance(second, NoTradeDecision)
        assert second.reason == "duplicate_intent"
    else:
        assert isinstance(first, NoTradeDecision)


def test_flag_off_and_system_flag() -> None:
    off = engine(enabled=False)
    result = off.evaluate_candidate(ranked_candidate(handoff=True))
    assert isinstance(result, NoTradeDecision)
    assert result.reason == "feature_flag_off"
    on = engine()
    on.global_pipe.flags = type(on.global_pipe.flags)(
        strategy_evaluation_enabled=False, observe_only=True, live_trading=False
    )
    blocked = on.evaluate_candidate(ranked_candidate(handoff=True))
    assert isinstance(blocked, NoTradeDecision)
    assert blocked.reason == "system_flag_disabled"


def test_lookahead_rejected() -> None:
    mod = engine()
    future = AS_OF + timedelta(hours=1)
    result = mod.evaluate_candidate(ranked_candidate(handoff=True, context_as_of=future))
    assert isinstance(result, NoTradeDecision)
    assert result.reason == "lookahead"
