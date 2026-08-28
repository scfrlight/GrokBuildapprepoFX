"""OMS state machine, fills, cancel/modify, terminal protection."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from botmoduleproject1.contracts.v1.execution import (
    ExecutionLifecycleState,
    FillEvent,
    OrderLifecycleEvent,
    OrderRecord,
)
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig
from botmoduleproject1.modules.pm5_execution.oms.core import OrderLifecycleManager
from botmoduleproject1.modules.pm5_execution.oms.state_machine import IllegalTransition, apply_transition
from tests.unit.pm5_support import ingest_allow, pm5_module

NOW = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


def _record(state: ExecutionLifecycleState, qty: str = "1.00") -> OrderRecord:
    oid = uuid4()
    q = Decimal(qty)
    return OrderRecord(
        order_id=oid,
        intent_id=uuid4(),
        pm4_decision_id=uuid4(),
        idempotency_key=str(oid),
        correlation_id=oid,
        occurred_at=NOW,
        symbol="EURUSD",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
        original_quantity=q,
        remaining_quantity=q,
        state=state,
    )


def _seed(mgr: OrderLifecycleManager, record: OrderRecord) -> OrderRecord:
    event = OrderLifecycleEvent(
        order_id=record.order_id,
        occurred_at=NOW,
        to_state=record.state,
        reason="seed",
        actor="test",
        source="oms",
    )
    mgr.put_new(record, event)
    return record


def test_valid_transitions() -> None:
    rec = _record(ExecutionLifecycleState.INTENT_CREATED)
    nxt, _ = apply_transition(rec, ExecutionLifecycleState.VALIDATED, now=NOW, reason="ok", actor="t")
    assert nxt.state is ExecutionLifecycleState.VALIDATED


def test_invalid_transition_rejected() -> None:
    rec = _record(ExecutionLifecycleState.INTENT_CREATED)
    with pytest.raises(IllegalTransition):
        apply_transition(rec, ExecutionLifecycleState.FILLED, now=NOW, reason="no", actor="t")


def test_terminal_state_protected() -> None:
    rec = _record(ExecutionLifecycleState.REJECTED)
    with pytest.raises(IllegalTransition, match="terminal"):
        apply_transition(rec, ExecutionLifecycleState.QUEUED, now=NOW, reason="no", actor="t")


def test_partial_and_full_fill() -> None:
    mgr = OrderLifecycleManager()
    rec = _seed(mgr, _record(ExecutionLifecycleState.ACKNOWLEDGED, "1.00"))
    half = FillEvent(order_id=rec.order_id, occurred_at=NOW, quantity=Decimal("0.40"), price=Decimal("1.1"), source="simulation")
    rec = mgr.apply_fill(rec, half, now=NOW)
    assert rec.state is ExecutionLifecycleState.PARTIALLY_FILLED
    assert rec.filled_quantity == Decimal("0.40")
    assert rec.remaining_quantity == Decimal("0.60")
    rest = FillEvent(order_id=rec.order_id, occurred_at=NOW, quantity=Decimal("0.60"), price=Decimal("1.1"), source="simulation")
    rec = mgr.apply_fill(rec, rest, now=NOW)
    assert rec.state is ExecutionLifecycleState.FILLED
    assert rec.remaining_quantity == Decimal("0")
    assert rec.filled_quantity == Decimal("1.00")


def test_cancel_lifecycle() -> None:
    cfg = Pm5ExecutionConfig(operating_mode="simulation", simulation_auto_fill=False)
    mod, _b, pub = ingest_allow(pm5_module(config=cfg), key="cancel-1")
    assert pub.order.state is ExecutionLifecycleState.ACKNOWLEDGED
    cancelled = mod.cancel_order(pub.order.order_id, reason="test_cancel")
    assert cancelled.state is ExecutionLifecycleState.CANCELLED
    states = [e.to_state for e in mod.get_order_timeline(pub.order.order_id)]
    assert ExecutionLifecycleState.CANCEL_REQUESTED in states
    assert ExecutionLifecycleState.CANCELLED in states


def test_modify_lifecycle() -> None:
    mgr = OrderLifecycleManager()
    rec = _seed(mgr, _record(ExecutionLifecycleState.ACKNOWLEDGED))
    rec = mgr.transit(rec, ExecutionLifecycleState.MODIFY_REQUESTED, now=NOW, reason="modify", actor="t")
    rec = mgr.transit(rec, ExecutionLifecycleState.MODIFIED, now=NOW, reason="modified", actor="t")
    assert rec.state is ExecutionLifecycleState.MODIFIED


def test_expiry_and_recon_pending() -> None:
    mgr = OrderLifecycleManager()
    rec = _seed(mgr, _record(ExecutionLifecycleState.ACKNOWLEDGED))
    rec = mgr.transit(rec, ExecutionLifecycleState.EXPIRED, now=NOW, reason="ttl", actor="t")
    rec = mgr.transit(rec, ExecutionLifecycleState.RECONCILIATION_PENDING, now=NOW, reason="recon", actor="t")
    assert rec.state is ExecutionLifecycleState.RECONCILIATION_PENDING
    rec = mgr.transit(rec, ExecutionLifecycleState.MISMATCH_DETECTED, now=NOW, reason="delta", actor="t")
    rec = mgr.transit(rec, ExecutionLifecycleState.RECOVERY_PENDING, now=NOW, reason="recover", actor="t")
    assert rec.state is ExecutionLifecycleState.RECOVERY_PENDING


def test_deterministic_event_history() -> None:
    mgr = OrderLifecycleManager()
    rec = _seed(mgr, _record(ExecutionLifecycleState.INTENT_CREATED))
    rec = mgr.transit(rec, ExecutionLifecycleState.VALIDATED, now=NOW, reason="v", actor="t")
    rec = mgr.transit(rec, ExecutionLifecycleState.QUEUED, now=NOW, reason="q", actor="t")
    events = mgr.events(rec.order_id)
    assert [e.to_state for e in events] == [
        ExecutionLifecycleState.INTENT_CREATED,
        ExecutionLifecycleState.VALIDATED,
        ExecutionLifecycleState.QUEUED,
    ]
    assert mgr.events(rec.order_id) == events
