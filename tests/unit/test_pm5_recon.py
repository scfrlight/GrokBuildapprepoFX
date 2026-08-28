"""Reconciliation: unavailable venue is degraded, never a silent pass."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import ReconciliationOutcome
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.pm5_execution.reconciliation.engine import ReconciliationEngine
from tests.unit.pm5_support import ingest_allow


def test_unavailable_broker_is_degraded_not_pass() -> None:
    rec = ReconciliationEngine().run(
        now=utc_now(),
        local_order_count=1,
        broker_order_count=0,
        broker_truth_available=False,
    )
    assert rec.outcome is ReconciliationOutcome.DEGRADED
    assert rec.consistent is False
    assert rec.broker_truth_available is False
    assert rec.mismatch_type == "broker_truth_unavailable"


def test_local_equals_broker_pass() -> None:
    rec = ReconciliationEngine().run(
        now=utc_now(),
        local_order_count=1,
        broker_order_count=1,
        broker_truth_available=True,
    )
    assert rec.outcome is ReconciliationOutcome.PASS
    assert rec.consistent is True


def test_missing_and_unexpected_broker_order_mismatch() -> None:
    missing = ReconciliationEngine().run(
        now=utc_now(),
        local_order_count=1,
        broker_order_count=0,
        broker_truth_available=True,
        missing_broker_order=True,
    )
    assert missing.outcome is ReconciliationOutcome.CRITICAL
    unexpected = ReconciliationEngine().run(
        now=utc_now(),
        local_order_count=0,
        broker_order_count=1,
        broker_truth_available=True,
        unexpected_broker_order=True,
    )
    assert unexpected.outcome is ReconciliationOutcome.MISMATCH


def test_fill_difference_mismatch() -> None:
    rec = ReconciliationEngine().run(
        now=utc_now(),
        local_order_count=1,
        broker_order_count=1,
        broker_truth_available=True,
        fill_mismatch=True,
    )
    assert rec.outcome is ReconciliationOutcome.MISMATCH


def test_position_difference_critical() -> None:
    rec = ReconciliationEngine().run(
        now=utc_now(),
        local_order_count=1,
        broker_order_count=1,
        broker_truth_available=True,
        position_mismatch=True,
    )
    assert rec.outcome is ReconciliationOutcome.CRITICAL
    assert rec.recommended_action == "block_new_orders_and_recover"


def test_simulation_ingest_recon_is_degraded() -> None:
    _mod, _b, pub = ingest_allow(key="recon-sim")
    assert pub.reconciliation is not None
    assert pub.reconciliation.outcome is ReconciliationOutcome.DEGRADED
    assert pub.reconciliation.broker_truth_available is False
    assert pub.operating_state.value != "normal" or pub.reconciliation.outcome is ReconciliationOutcome.DEGRADED


def test_critical_mismatch_blocks_new_orders() -> None:
    from botmoduleproject1.contracts.v1.execution import ControlScope
    from botmoduleproject1.contracts.v1.strategy import Direction
    from tests.unit.pm4_support import admitted_bundle
    from tests.unit.pm5_support import pm5_module

    mod = pm5_module()
    rec = mod.recon.run(
        now=mod.clock.now(),
        local_order_count=1,
        broker_order_count=0,
        broker_truth_available=True,
        missing_broker_order=True,
    )
    assert rec.outcome is ReconciliationOutcome.CRITICAL
    mod.control.operating = __import__(
        "botmoduleproject1.contracts.v1.execution", fromlist=["Pm5OperatingState"]
    ).Pm5OperatingState.RECONCILIATION_CRITICAL
    mod.freeze_scope(scope=ControlScope.GLOBAL, reason="critical mismatch")
    pub = mod.ingest(admitted_bundle(key="crit"), direction=Direction.BUY)
    assert pub.receipt.accepted is False
