"""Independent control plane, kill-switch, freeze, recovery."""

from __future__ import annotations

from datetime import timedelta

from botmoduleproject1.contracts.v1.execution import (
    ControlScope,
    ExecutionRejectReason,
    Pm5OperatingState,
)
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig
from tests.unit.pm4_support import AS_OF, admitted_bundle
from tests.unit.pm5_support import Clock, ingest_allow, pm5_module


def test_symbol_and_global_freeze() -> None:
    mod = pm5_module()
    mod.freeze_scope(scope=ControlScope.SYMBOL, reason="freeze EURUSD", scope_id="EURUSD")
    bundle = admitted_bundle(key="frz")
    pub = mod.ingest(bundle, direction=Direction.BUY)
    assert ExecutionRejectReason.CONTROL_BLOCKED in pub.receipt.reasons


def test_strategy_cluster_account_freeze() -> None:
    mod = pm5_module()
    mod.freeze_scope(scope=ControlScope.STRATEGY, reason="s", scope_id="trend_pullback")
    mod.freeze_scope(scope=ControlScope.CLUSTER, reason="c", scope_id="EUR|USD")
    mod.freeze_scope(scope=ControlScope.ACCOUNT, reason="a", scope_id="account")
    assert mod.control.blocks("EURUSD", "trend_pullback", "EUR|USD") is True
    assert mod.control.operating is Pm5OperatingState.FREEZE_NEW_ORDERS


def test_close_only_and_no_new_risk() -> None:
    mod = pm5_module()
    mod.enter_close_only(reason="session end")
    pub = mod.ingest(admitted_bundle(key="co"), direction=Direction.BUY)
    assert ExecutionRejectReason.CONTROL_BLOCKED in pub.receipt.reasons
    mod2 = pm5_module()
    mod2.no_new_risk(reason="heat")
    pub2 = mod2.ingest(admitted_bundle(key="nnr"), direction=Direction.BUY)
    assert ExecutionRejectReason.CONTROL_BLOCKED in pub2.receipt.reasons


def test_emergency_cancel_latches() -> None:
    cfg = Pm5ExecutionConfig(operating_mode="simulation", simulation_auto_fill=False)
    mod, _b, pub = ingest_allow(pm5_module(config=cfg), key="emg")
    rec = mod.emergency_cancel(reason="operator halt")
    assert rec.action.value == "emergency_cancel"
    assert mod.control.kill_latched is True
    blocked = mod.ingest(admitted_bundle(key="emg-2"), direction=Direction.BUY)
    assert ExecutionRejectReason.CONTROL_BLOCKED in blocked.receipt.reasons


def test_manual_recovery_requires_reason() -> None:
    mod = pm5_module()
    mod.emergency_cancel(reason="halt")
    empty = mod.request_recovery(reason="   ")
    assert empty.action.value == "recovery_request"
    assert mod.control.kill_latched is True


def test_no_hidden_auto_rearm_cooldown() -> None:
    clock = Clock(AS_OF)
    cfg = Pm5ExecutionConfig(operating_mode="simulation", recovery_cooldown_seconds=300)
    mod = pm5_module(config=cfg, clock=clock)
    mod.emergency_cancel(reason="halt")
    cool = mod.request_recovery(reason="too soon")
    assert cool.result == "cooldown"
    assert mod.control.kill_latched is True
    clock.set(AS_OF + timedelta(seconds=301))
    ok = mod.request_recovery(reason="reviewed by desk")
    assert ok.action.value == "reenable"
    assert mod.control.kill_latched is False


def test_kill_switch_from_pm4_bundle() -> None:
    from tests.unit.pm4_support import make_candidate, make_forecast, make_intent, make_exposure, risk_module

    gate = risk_module()
    gate.trip_kill_switch("pm4 trip")
    cand = make_candidate()
    intent = make_intent(key="ks", candidate_id=cand.candidate_id)
    bundle = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=cand,
        forecast=make_forecast(intent),
        mid_price=intent.entry_price,
        session="london",
    )
    pub = pm5_module().ingest(bundle, direction=Direction.BUY)
    assert ExecutionRejectReason.KILL_SWITCH in pub.receipt.reasons or ExecutionRejectReason.PM4_DENY in pub.receipt.reasons
