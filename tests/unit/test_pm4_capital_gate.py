"""PM4 capital-management gate. Deny-by-default. Never an order."""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.pm4_capital import (
    CapitalDecisionState,
    CapitalEvaluationResult,
    CheckStatus,
    QuantileBand,
    RiskApprovedExecutableIntent,
    RiskEvaluationRequest,
)
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm4_risk_gate.capital.boundary import (
    FORBIDDEN_SURFACE,
    execution_allowed,
    trading_readiness,
)
from botmoduleproject1.modules.pm4_risk_gate.capital.catalog import CHECK_CATALOG
from botmoduleproject1.modules.pm4_risk_gate.capital.evaluation import CapitalEvaluationService
from botmoduleproject1.modules.pm4_risk_gate.capital.safe_halt import SafeHaltController
from botmoduleproject1.modules.pm4_risk_gate.capital.sizing import size_position
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.module import PM4RiskGateModule
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
from botmoduleproject1.modules.pm8_persistence.money import MoneyError
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore
from tests.unit.pm4_support import _Clock, admitted_bundle, make_forecast, make_intent, risk_module

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)
CAPITAL_ROOT = Path(__file__).resolve().parents[2] / "botmoduleproject1" / "modules" / "pm4_risk_gate" / "capital"


def _band() -> QuantileBand:
    return QuantileBand(
        q05=Decimal("1.09600"),
        q25=Decimal("1.09800"),
        q50=Decimal("1.10000"),
        q75=Decimal("1.10200"),
        q95=Decimal("1.10400"),
    )


def make_request(**overrides) -> RiskEvaluationRequest:
    payload = dict(
        request_id=str(uuid4()),
        idempotency_key=overrides.pop("idempotency_key", f"cap-{uuid4().hex[:10]}"),
        correlation_id=str(uuid4()),
        causation_id=str(uuid4()),
        trade_intent_id=str(uuid4()),
        strategy_id="trend_pullback",
        strategy_version="v1",
        profile_id="trend_pullback",
        profile_version="v1",
        symbol="EURUSD",
        timeframe="H1",
        side="buy",
        requested_quantity=Decimal("1.00"),
        entry_price=Decimal("1.10000"),
        stop_loss_price=Decimal("1.09500"),
        take_profit_price=Decimal("1.11000"),
        signal_timestamp=AS_OF,
        intent_created_at=AS_OF,
        market_snapshot_id="mkt-1",
        regime_snapshot_id="reg-1",
        model_snapshot_id="model-1",
        model_version="0.1.0",
        model_quality_status="ok",
        predicted_quantiles=_band(),
        expected_return=None,
        spread=Decimal("0.00010"),
        estimated_slippage=Decimal("0.00010"),
        estimated_commission=Decimal("2"),
        account_snapshot_id="acct-1",
        portfolio_snapshot_id="port-1",
        current_positions_snapshot_id="pos-1",
        current_orders_snapshot_id="ord-1",
        risk_policy_version="1.0.0",
        execution_policy_version="sim-1",
        account_equity=Decimal("100000"),
        peak_equity=Decimal("100000"),
        free_margin=Decimal("100000"),
        conversion_rate=Decimal("1"),
        contract_size=Decimal("100000"),
        volume_step=Decimal("0.01"),
        session="london",
        regime="trending",
        market_age_seconds=1,
        account_age_seconds=1,
        portfolio_age_seconds=1,
        model_age_seconds=1,
        reconciliation_status="ok",
        control_state="active",
        persistence_available=True,
    )
    payload.update(overrides)
    return RiskEvaluationRequest(**payload)


def service(config: Pm4RiskGateConfig | None = None, *, persistence=None) -> CapitalEvaluationService:
    return CapitalEvaluationService(
        config or Pm4RiskGateConfig(),
        clock=_Clock(AS_OF),
        persistence=persistence,
        require_persistence=persistence is not None,
    )


def _sqlite(tmp_path: Path) -> PersistenceApiV1:
    return PersistenceApiV1(SqliteStore(tmp_path / "capital.sqlite"))


def test_catalog_has_exactly_forty_named_checks() -> None:
    assert len(CHECK_CATALOG) == 40
    assert len(set(CHECK_CATALOG)) == 40
    assert CHECK_CATALOG[0] == "input_schema"
    assert CHECK_CATALOG[-1] == "global_safe_halt"
    root = Path(__file__).resolve().parents[2]
    assert not (root / "botmoduleproject1" / "modules" / "pm5_risk_capital_gate").exists()
    assert not (root / "docs" / "architecture" / "sequence_15_report.md").exists()


def test_happy_path_emits_all_forty_checks_and_no_execution() -> None:
    result = service().evaluate(make_request())
    assert result.decision.final_decision in {
        CapitalDecisionState.APPROVED,
        CapitalDecisionState.APPROVED_REDUCED_SIZE,
    }
    assert len(result.decision.checks) == 40
    assert [c.name for c in result.decision.checks] == list(CHECK_CATALOG)
    assert result.executable_intent is not None
    assert result.executable_intent.execution_allowed is False
    assert result.executable_intent.creates_order is False
    assert result.decision.execution_permitted is False
    assert result.decision.trading_readiness is False
    assert result.decision.approved_quantity > 0
    assert result.decision.sizing is not None
    assert result.decision.sizing.rounded_size == result.decision.approved_quantity


def test_module_evaluate_capital_matches_service() -> None:
    gate = PM4RiskGateModule(Pm4RiskGateConfig(), _Clock(AS_OF), feature_enabled=True)
    result = gate.evaluate_capital(make_request())
    assert isinstance(result, CapitalEvaluationResult)
    assert result.decision.execution_permitted is False
    assert execution_allowed() is False
    assert trading_readiness() is False


def test_existing_evaluate_path_unchanged() -> None:
    bundle = admitted_bundle(key="capital-does-not-break-seq06")
    assert bundle.execution_permitted is False
    src = inspect.getsource(PM4RiskGateModule)
    assert "OrderRequest" not in src
    assert "submit(" not in src


def test_float_money_rejected() -> None:
    with pytest.raises((ValidationError, MoneyError, ValueError)):
        make_request(entry_price=1.1)  # type: ignore[arg-type]


def test_nan_money_rejected() -> None:
    with pytest.raises((ValidationError, MoneyError, ValueError)):
        make_request(account_equity=Decimal("NaN"))


def test_side_must_be_buy_or_sell() -> None:
    with pytest.raises(ValidationError):
        make_request(side="long")


def test_missing_stop_fails_closed() -> None:
    result = service().evaluate(make_request(stop_loss_price=Decimal("1.10000")))
    assert result.decision.final_decision not in {
        CapitalDecisionState.APPROVED,
        CapitalDecisionState.APPROVED_REDUCED_SIZE,
    }
    assert result.executable_intent is None
    assert result.decision.approved_quantity == 0
    assert "stop_loss_existence" in result.decision.failed_checks or "position_size_validity" in result.decision.failed_checks


def test_sizing_never_rounds_up_through_budget() -> None:
    cfg = Pm4RiskGateConfig()
    req = make_request(requested_quantity=Decimal("5.00"))
    trace = size_position(
        req,
        cfg,
        heat_headroom=Decimal("0.020"),
        remaining_trade_budget=req.account_equity * cfg.max_per_trade_risk_pct,
    )
    step = cfg.lot_step
    rounded_down = trace.constrained_size.quantize(step, rounding=ROUND_DOWN)
    rounded_up = trace.constrained_size.quantize(step, rounding=ROUND_HALF_UP)
    assert trace.rounded_size == rounded_down
    assert trace.rounded_size <= trace.constrained_size
    cap = req.account_equity * cfg.max_per_trade_risk_pct
    assert trace.final_risk <= cap
    if rounded_up > rounded_down:
        up_risk = rounded_up * (trace.effective_stop * (req.contract_size or cfg.contract_size) * (req.conversion_rate or Decimal("1")))
        # ROUND_DOWN is what keeps us inside the post-commission budget.
        assert trace.rounded_size < rounded_up or up_risk <= cap


def test_heat_blocks_when_projected_exceeds_cap() -> None:
    req = make_request(
        open_position_risk=Decimal("1800"),
        pending_order_risk=Decimal("200"),
        requested_quantity=Decimal("1.00"),
    )
    result = service().evaluate(req)
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_PORTFOLIO_HEAT
    assert result.executable_intent is None
    assert "portfolio_heat" in result.decision.failed_checks


def test_drawdown_freeze_blocks_and_trips_halt() -> None:
    svc = service()
    req = make_request(account_equity=Decimal("91000"), peak_equity=Decimal("100000"))
    result = svc.evaluate(req)
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_DRAWDOWN
    assert svc.halt.halted is True
    with pytest.raises(ValueError, match="non-automatic"):
        svc.halt.recover(actor="automatic", reason="nope")
    svc.halt.recover(actor="operator", reason="manual review")
    assert svc.halt.halted is False


def test_drawdown_survives_restart(tmp_path: Path) -> None:
    api = _sqlite(tmp_path)
    first = service(persistence=api)
    ok = first.evaluate(make_request(idempotency_key="dd-1", account_equity=Decimal("100000"), peak_equity=Decimal("100000")))
    assert ok.decision.final_decision in {
        CapitalDecisionState.APPROVED,
        CapitalDecisionState.APPROVED_REDUCED_SIZE,
    }
    restarted = service(persistence=api)
    silent_reset = restarted.evaluate(
        make_request(
            idempotency_key="dd-2",
            account_equity=Decimal("91000"),
            peak_equity=Decimal("91000"),
        )
    )
    assert silent_reset.decision.final_decision is CapitalDecisionState.BLOCKED_DRAWDOWN
    assert restarted.ledger.peak_equity == Decimal("100000")


def test_stale_market_blocks() -> None:
    result = service().evaluate(make_request(market_age_seconds=120))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_DATA
    assert "market_freshness" in result.decision.failed_checks


def test_unknown_exposure_fail_closed() -> None:
    result = service().evaluate(make_request(exposure_unknown=True))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_DATA
    assert result.executable_intent is None


def test_unknown_reconciliation_blocks() -> None:
    result = service().evaluate(make_request(reconciliation_status="unknown"))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_RECONCILIATION


def test_model_quality_unknown_blocks_when_required() -> None:
    result = service().evaluate(make_request(model_quality_status="unknown"))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_MODEL
    assert "model_quality" in result.decision.failed_checks


def test_wide_uncertainty_blocks() -> None:
    wide = QuantileBand(
        q05=Decimal("1.08000"),
        q25=Decimal("1.09000"),
        q50=Decimal("1.10000"),
        q75=Decimal("1.11000"),
        q95=Decimal("1.13000"),
    )
    result = service().evaluate(make_request(predicted_quantiles=wide))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_MODEL
    assert "model_uncertainty" in result.decision.failed_checks


def test_spread_gate() -> None:
    result = service().evaluate(make_request(spread=Decimal("0.00100")))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_SPREAD


def test_safe_halt_latch_no_auto_rearm() -> None:
    halt = SafeHaltController()
    halt.trip("manual")
    with pytest.raises(ValueError):
        halt.recover(actor="automatic", reason="x")
    assert halt.halted is True
    result = service().evaluate(make_request(safe_halt=True))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_SYSTEM
    assert result.executable_intent is None


def test_idempotency_same_key_same_hash_returns_stored() -> None:
    svc = service()
    req = make_request(idempotency_key="same-key")
    a = svc.evaluate(req)
    b = svc.evaluate(req)
    assert a.decision.decision_id == b.decision.decision_id
    assert a.decision.output_hash == b.decision.output_hash


def test_idempotency_same_key_different_hash_conflicts() -> None:
    svc = service()
    svc.evaluate(make_request(idempotency_key="conflict-key", requested_quantity=Decimal("1.00")))
    with pytest.raises(ValueError, match="idempotency conflict"):
        svc.evaluate(make_request(idempotency_key="conflict-key", requested_quantity=Decimal("0.50")))


def test_persist_round_trip_sqlite(tmp_path: Path) -> None:
    api = _sqlite(tmp_path)
    svc = service(persistence=api)
    req = make_request(idempotency_key="persist-1")
    first = svc.evaluate(req)
    assert first.decision.persistence_reference
    events = api.store.list_events(limit=1000)
    kinds = {ev["event_type"] for ev in events}
    assert "risk.decision.committed" in kinds
    assert "risk.drawdown.snapshot" in kinds
    restarted = service(persistence=api)
    again = restarted.evaluate(req)
    assert again.decision.decision_id == first.decision.decision_id
    assert again.decision.output_hash == first.decision.output_hash


def test_replay_matches_and_does_not_overwrite(tmp_path: Path) -> None:
    api = _sqlite(tmp_path)
    svc = service(persistence=api)
    req = make_request(idempotency_key="replay-1")
    original = svc.evaluate(req)
    replayed = svc.replay(original, req)
    assert replayed.replay_match is True
    assert replayed.decision.output_hash == original.decision.output_hash
    kinds = [ev["event_type"] for ev in api.store.list_events(limit=1000)]
    assert "risk.replay.divergence" not in kinds


def test_injected_faults_fail_closed() -> None:
    for point in (
        "before_policy",
        "during_sizing",
        "during_heat",
        "before_persist",
        "after_commit",
    ):
        svc = service()
        svc.inject_fault = point
        result = svc.evaluate(make_request(idempotency_key=f"fault-{point}"))
        assert result.decision.final_decision is CapitalDecisionState.ERROR_FAIL_CLOSED
        assert result.executable_intent is None
        assert result.decision.approved_quantity == 0
        assert len(result.decision.checks) == 40


def test_persistence_unavailable_blocks() -> None:
    result = service().evaluate(make_request(persistence_available=False))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_SYSTEM
    assert "persistence_availability" in result.decision.failed_checks


def test_approved_intent_cannot_set_execution_allowed() -> None:
    result = service().evaluate(make_request())
    payload = result.executable_intent.model_dump()
    payload["execution_allowed"] = True
    with pytest.raises(ValidationError, match="execution"):
        RiskApprovedExecutableIntent(**payload)


def test_capital_package_has_no_broker_surface() -> None:
    blob = ""
    for path in CAPITAL_ROOT.rglob("*.py"):
        if path.name == "boundary.py":
            continue
        blob += path.read_text(encoding="utf-8")
    assert "OrderSend" not in blob
    assert "MetaTrader5" not in blob
    assert "order_send" not in blob
    assert "telegram.Bot" not in blob
    src = inspect.getsource(PM4RiskGateModule)
    assert "OrderSend" not in src
    assert "MetaTrader5" not in src
    assert "submit(" not in src
    assert execution_allowed() is False


def test_adapter_from_intent_uses_exit_plan() -> None:
    from botmoduleproject1.modules.pm4_risk_gate.capital.adapters import request_from_intent

    intent = make_intent(key="adapter-1")
    forecast = make_forecast(intent)
    req = request_from_intent(
        intent,
        equity=Decimal("100000"),
        peak_equity=Decimal("100000"),
        spread=Decimal("0.00010"),
        as_of=AS_OF,
        forecast=forecast,
        model_quality_status="ok",
        model_age_seconds=1,
        market_age_seconds=1,
        account_age_seconds=1,
        estimated_commission=Decimal("2"),
        contract_size=Decimal("100000"),
        volume_step=Decimal("0.01"),
        conversion_rate=Decimal("1"),
        take_profit_price=Decimal("1.10800"),
    )
    assert req.take_profit_price == Decimal("1.10800")
    assert req.stop_loss_price == Decimal("1.09500")
    assert req.side == "buy"
    result = service().evaluate(req)
    assert result.decision.final_decision in {
        CapitalDecisionState.APPROVED,
        CapitalDecisionState.APPROVED_REDUCED_SIZE,
        CapitalDecisionState.REJECTED,
    }
    assert result.decision.execution_permitted is False


def test_daily_loss_limit() -> None:
    result = service().evaluate(make_request(realized_pnl_day=Decimal("-2500")))
    assert result.decision.final_decision is CapitalDecisionState.BLOCKED_DRAWDOWN
    assert "daily_loss_limit" in result.decision.failed_checks


def test_duplicate_same_side_position() -> None:
    result = service().evaluate(make_request(existing_symbol_side="buy"))
    assert result.decision.final_decision is CapitalDecisionState.REJECTED
    assert "duplicate_position" in result.decision.failed_checks


def test_cooldown_defers() -> None:
    result = service().evaluate(make_request(cooldown_until=AS_OF + timedelta(minutes=10)))
    assert result.decision.final_decision is CapitalDecisionState.DEFERRED
    assert result.executable_intent is None


def test_all_checks_run_on_fail_closed() -> None:
    svc = service()
    svc.inject_fault = "before_policy"
    result = svc.evaluate(make_request())
    assert [c.name for c in result.decision.checks] == list(CHECK_CATALOG)
    assert all(c.status is CheckStatus.BLOCK for c in result.decision.checks)
