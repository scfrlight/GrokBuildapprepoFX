"""PM5 intake: PM4-only authorization, freshness, quantity cap, duplicates."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import ExecutionRejectReason
from botmoduleproject1.contracts.v1.risk import RiskVerdictStatus
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.modules.pm5_execution.intake.validators import approved_quantity
from tests.unit.pm4_support import AS_OF, admitted_bundle, make_exposure, make_intent, risk_module
from tests.unit.pm5_support import Clock, ingest_allow, pm5_module


def test_simulation_accepts_pm4_allow() -> None:
    _mod, bundle, pub = ingest_allow(key="pm5-allow")
    assert bundle.verdict.status is RiskVerdictStatus.ALLOW
    assert bundle.execution_permitted is False
    assert pub.receipt.accepted is True
    assert pub.broker_side_effect is False
    assert pub.mt5_used is False
    assert pub.order is not None
    assert pub.order.simulation is True
    assert pub.order.broker_ticket is not None
    assert pub.order.broker_ticket.startswith("SIM-")


def test_missing_pm4_authorization_rejected() -> None:
    pub = pm5_module().ingest(None, direction=Direction.BUY)
    assert pub.receipt.accepted is False
    assert ExecutionRejectReason.MISSING_AUTHORIZATION in pub.receipt.reasons


def test_pm4_deny_rejected() -> None:
    gate = risk_module()
    bundle = gate.evaluate_intent(make_intent(key="deny-pm4"), make_exposure())
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    pub = pm5_module().ingest(bundle, direction=Direction.BUY, entry_type=EntryType.MARKET)
    assert pub.receipt.accepted is False
    assert ExecutionRejectReason.PM4_DENY in pub.receipt.reasons
    assert pub.broker_side_effect is False


def test_execution_permitted_false_rejected_on_broker_path() -> None:
    mod, bundle, pub = ingest_allow(key="broker-path")
    assert bundle.execution_permitted is False
    assert pub.receipt.accepted is True
    refused = mod.broker_submit(pub.order.order_id)
    assert refused.accepted is False
    assert ExecutionRejectReason.EXECUTION_NOT_PERMITTED in refused.reasons
    assert refused.broker_side_effect is False


def test_stale_intent_rejected() -> None:
    clock = Clock(AS_OF)
    mod = pm5_module(clock=clock)
    bundle = admitted_bundle(key="stale")
    clock.set(AS_OF + timedelta(hours=5))
    pub = mod.ingest(bundle, direction=Direction.BUY)
    assert ExecutionRejectReason.STALE_INTENT in pub.receipt.reasons
    assert pub.receipt.accepted is False


def test_future_timestamp_rejected() -> None:
    clock = Clock(AS_OF)
    mod = pm5_module(clock=clock)
    bundle = admitted_bundle(key="future")
    # bundle is at AS_OF; move clock backward so bundle looks like lookahead
    clock.set(AS_OF - timedelta(minutes=5))
    pub = mod.ingest(bundle, direction=Direction.BUY)
    assert ExecutionRejectReason.LOOKAHEAD in pub.receipt.reasons


def test_invalid_quantity_rejected() -> None:
    bundle = admitted_bundle(key="qty0")
    pub = pm5_module().ingest(bundle, direction=Direction.BUY, quantity=Decimal("0"))
    assert ExecutionRejectReason.INVALID_QUANTITY in pub.receipt.reasons


def test_quantity_above_pm4_rejected() -> None:
    bundle = admitted_bundle(key="qty-cap")
    cap = approved_quantity(bundle)
    pub = pm5_module().ingest(bundle, direction=Direction.BUY, quantity=cap + Decimal("1"))
    assert ExecutionRejectReason.QUANTITY_EXCEEDS_PM4 in pub.receipt.reasons
    assert pub.receipt.accepted is False


def test_invalid_order_type_rejected() -> None:
    bundle = admitted_bundle(key="iceberg")
    pub = pm5_module().ingest(bundle, direction=Direction.BUY, order_type="iceberg")
    assert ExecutionRejectReason.INVALID_ORDER_TYPE in pub.receipt.reasons


def test_unsupported_symbol_rejected() -> None:
    from tests.unit.pm4_support import make_candidate, make_forecast

    gate = risk_module()
    cand = make_candidate(symbol="XAUUSD")
    intent = make_intent(key="xau", symbol="XAUUSD", candidate_id=cand.candidate_id)
    bundle = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=cand,
        forecast=make_forecast(intent),
        mid_price=Decimal("1.10000"),
        session="london",
    )
    pub = pm5_module().ingest(bundle, direction=Direction.BUY)
    assert ExecutionRejectReason.UNSUPPORTED_SYMBOL in pub.receipt.reasons


def test_duplicate_idempotency_replays() -> None:
    mod = pm5_module()
    _m, _b, first = ingest_allow(mod, key="dup-1")
    _m, _b, second = ingest_allow(mod, key="dup-1")
    assert second.receipt.idempotent_replay is True
    assert first.order.order_id == second.order.order_id


def test_duplicate_conflict_on_payload_mismatch() -> None:
    mod = pm5_module()
    bundle = admitted_bundle(key="dup-2")
    first = mod.ingest(bundle, direction=Direction.BUY, quantity=None)
    assert first.receipt.accepted is True
    second = mod.ingest(bundle, direction=Direction.SELL)
    assert ExecutionRejectReason.DUPLICATE_CONFLICT in second.receipt.reasons


def test_missing_traceability_rejected() -> None:
    bundle = admitted_bundle(key="trace")
    stripped = bundle.model_copy(update={"idempotency_key": ""})
    pub = pm5_module().ingest(stripped, direction=Direction.BUY)
    assert ExecutionRejectReason.MISSING_TRACE in pub.receipt.reasons


def test_unsupported_side_rejected() -> None:
    bundle = admitted_bundle(key="side")
    pub = pm5_module().ingest(bundle, direction=None)
    assert ExecutionRejectReason.UNSUPPORTED_SIDE in pub.receipt.reasons
