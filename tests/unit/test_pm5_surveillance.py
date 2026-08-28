"""Surveillance bursts, throttles, quality, replay, exposure."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import ExecutionRejectReason, ReconciliationOutcome
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig
from tests.unit.pm4_support import admitted_bundle
from tests.unit.pm5_support import ingest_allow, pm5_module


def test_reject_burst_triggers_protection() -> None:
    cfg = Pm5ExecutionConfig(operating_mode="simulation", reject_burst=2)
    mod = pm5_module(config=cfg)
    for i in range(3):
        mod.ingest(None, direction=Direction.BUY)
    assert any(a.detector == "reject_burst" for a in mod.surv.alerts)
    assert mod.control.kill_latched is True


def test_submit_burst_throttles() -> None:
    cfg = Pm5ExecutionConfig(operating_mode="simulation", submit_burst=2)
    mod = pm5_module(config=cfg)
    for i in range(3):
        ingest_allow(mod, key=f"burst-{i}")
    assert any(a.detector == "submit_burst" for a in mod.surv.alerts)
    blocked = mod.ingest(admitted_bundle(key="burst-late"), direction=Direction.BUY)
    assert ExecutionRejectReason.CONTROL_BLOCKED in blocked.receipt.reasons


def test_cancel_and_modify_storms() -> None:
    cfg = Pm5ExecutionConfig(operating_mode="simulation", cancel_burst=1, modify_burst=1)
    mod = pm5_module(config=cfg)
    now = mod.clock.now()
    assert mod.surv.note_cancel(now) is None
    storm = mod.surv.note_cancel(now)
    assert storm is not None and storm.detector == "cancel_storm"
    assert mod.surv.note_modify(now) is None
    mstorm = mod.surv.note_modify(now)
    assert mstorm is not None and mstorm.detector == "modify_storm"
    assert storm.automatic_protection is True
    assert storm.recommended_action


def test_quality_insufficient_data_stays_null() -> None:
    from datetime import datetime

    from botmoduleproject1.contracts.v1.time import UTC
    from botmoduleproject1.modules.pm5_execution.analytics.execution_quality import ExecutionQualityEngine

    report = ExecutionQualityEngine().report(None, (), (), now=datetime(2026, 1, 1, tzinfo=UTC), rejects=0, submits=0)
    assert report.data_status == "insufficient_data"
    assert report.realized_slippage is None


def test_quality_does_not_mutate_oms() -> None:
    mod, _b, pub = ingest_allow(key="qual")
    before = mod.get_order(pub.order.order_id)
    _ = mod.quality.report(
        before,
        mod.get_order_timeline(pub.order.order_id),
        tuple(mod._fills.get(str(pub.order.order_id), ())),
        now=mod.clock.now(),
        rejects=0,
        submits=1,
    )
    after = mod.get_order(pub.order.order_id)
    assert after == before


def test_replay_is_deterministic() -> None:
    mod, _b, pub = ingest_allow(key="replay")
    a = mod.get_replay_bundle(pub.order.order_id)
    b = mod.get_replay_bundle(pub.order.order_id)
    assert a.deterministic is True
    assert [e["kind"] for e in a.events] == [e["kind"] for e in b.events]
    assert a.events[0]["kind"] == "lifecycle"


def test_exposure_working_and_stale() -> None:
    mod, _b, pub = ingest_allow(key="exp")
    snap = mod.get_exposure()
    assert snap.broker_truth_available is False
    assert snap.stale is True
    assert snap.reconciliation_status is ReconciliationOutcome.DEGRADED
    assert snap.expected_exposure >= 0
    assert pub.exposure is not None
    assert pub.exposure.broker_exposure is None
