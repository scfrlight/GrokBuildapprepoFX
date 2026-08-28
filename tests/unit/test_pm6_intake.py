from datetime import timedelta

from botmoduleproject1.contracts.v1.execution import ExecutionIntentReceipt, ExecutionMode, ExecutionPublicationBundle
from botmoduleproject1.contracts.v1.post_trade import IntakeDisposition, TruthSource
from botmoduleproject1.modules.pm6_post_trade.intake.pm5_adapter import classify_truth
from tests.unit.pm4_support import AS_OF
from tests.unit.pm5_support import Clock, ingest_allow
from tests.unit.pm6_support import observe_allow, pm6_module


def test_valid_simulation_event_accepted() -> None:
    pm6, _risk, pub, truth = observe_allow()
    assert truth.intake.disposition in {IntakeDisposition.ACCEPTED, IntakeDisposition.DEGRADED}
    assert truth.truth_source is TruthSource.SIMULATION_TRUTH
    assert pub.order is not None
    assert str(pub.order.broker_ticket).startswith("SIM-")
    assert truth.broker_side_effect is False
    assert truth.mt5_used is False


def test_simulation_not_labelled_broker_truth() -> None:
    _pm6, _risk, pub, truth = observe_allow(key="pm6-sim")
    assert classify_truth(pub) is TruthSource.SIMULATION_TRUTH
    assert truth.snapshot.broker_truth_available is False
    assert truth.snapshot.reconciliation_status == "degraded"


def test_missing_source_quarantined() -> None:
    truth = pm6_module().observe(None, None)
    assert truth.intake.disposition is IntakeDisposition.QUARANTINED
    assert "missing_source" in truth.intake.reasons


def test_future_dated_rejected() -> None:
    clock = Clock(AS_OF)
    pm6 = pm6_module(clock=clock)
    _exe, bundle, pub = ingest_allow(key="pm6-future")
    clock.set(AS_OF - timedelta(minutes=5))
    truth = pm6.observe(pub, bundle)
    assert truth.intake.disposition is IntakeDisposition.REJECTED
    assert "future_dated" in truth.intake.reasons


def test_stale_quarantined() -> None:
    clock = Clock(AS_OF)
    pm6 = pm6_module(clock=clock)
    _exe, bundle, pub = ingest_allow(key="pm6-stale")
    clock.set(AS_OF + timedelta(hours=5))
    truth = pm6.observe(pub, bundle)
    assert truth.intake.disposition is IntakeDisposition.QUARANTINED
    assert "stale" in truth.intake.reasons


def test_missing_trace_rejected() -> None:
    pm6 = pm6_module()
    empty = ExecutionPublicationBundle(
        occurred_at=AS_OF,
        receipt=ExecutionIntentReceipt(accepted=False, detail="no-order"),
        execution_mode=ExecutionMode.SIMULATION,
    )
    truth = pm6.observe(empty, None)
    assert "missing_trace" in truth.intake.reasons
    assert truth.intake.disposition is IntakeDisposition.REJECTED


def test_feature_disabled_rejected() -> None:
    truth = pm6_module(feature_enabled=False).observe(None, None)
    assert truth.intake.disposition is IntakeDisposition.REJECTED
    assert "feature_disabled" in truth.intake.reasons
