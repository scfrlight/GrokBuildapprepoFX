"""Anti-bias and safety invariants for the PM3-Strategy Engine."""

from __future__ import annotations

from datetime import timedelta

from botmoduleproject1.contracts.v1.strategy import NoTradeDecision, TradeIntent
from botmoduleproject1.modules.pm3_strategy_engine.consensus.bayesian_adapter import BayesianUpdatePolicy
from tests.unit.pm3se_support import AS_OF, engine, ranked_candidate


def test_no_lookahead_future_context() -> None:
    mod = engine()
    result = mod.evaluate_candidate(
        ranked_candidate(handoff=True, context_as_of=AS_OF + timedelta(minutes=5))
    )
    assert isinstance(result, NoTradeDecision)
    assert result.reason == "lookahead"


def test_trade_intent_has_no_lot_size() -> None:
    mod = engine()
    result = mod.evaluate_candidate(ranked_candidate(handoff=True))
    if isinstance(result, TradeIntent):
        assert result.requested_volume is None
        assert not hasattr(result, "lot_size") or getattr(result, "lot_size", None) is None


def test_intent_is_not_order_and_no_risk_verdict() -> None:
    mod = engine()
    result = mod.evaluate_candidate(ranked_candidate(handoff=True))
    dumped = result.model_dump()
    blob = str(dumped)
    assert "OrderRequest" not in blob
    assert "RiskVerdict" not in blob
    assert "lot" not in blob.lower() or result.diagnostics.get("not_an_order") is True or isinstance(
        result, NoTradeDecision
    )


def test_confirmed_as_of_only() -> None:
    mod = engine()
    cand = ranked_candidate(handoff=True)
    assert cand.context.as_of <= cand.as_of
    result = mod.evaluate_candidate(cand)
    assert result.as_of == cand.as_of if isinstance(result, NoTradeDecision) else result.occurred_at == cand.as_of


def test_bayesian_disabled_identity() -> None:
    policy = BayesianUpdatePolicy()
    assert policy.enabled is False
    assert policy.update(0.4, 0.9) == 0.4


def test_deterministic_repeat() -> None:
    a = engine()
    b = engine()
    cand_a = ranked_candidate(handoff=True)
    # independent candidates — compare decision class on equivalent constructed scores
    r1 = a.evaluate_candidate(ranked_candidate(handoff=True, symbol="EURUSD"))
    r2 = b.evaluate_candidate(ranked_candidate(handoff=True, symbol="EURUSD"))
    assert type(r1) is type(r2)
    if isinstance(r1, TradeIntent) and isinstance(r2, TradeIntent):
        assert r1.direction is r2.direction
        assert r1.consensus is r2.consensus
