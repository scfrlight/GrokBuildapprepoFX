"""Kill-switch, degraded modes, recovery gate, governance/audit."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.journal import EventType
from botmoduleproject1.contracts.v1.risk import (
    KillSwitchScope,
    KillSwitchStatus,
    RecoveryStage,
    RiskMode,
    RiskRejectionReason,
    RiskVerdictStatus,
)
from tests.unit.pm4_support import (
    AS_OF,
    admitted_bundle,
    make_candidate,
    make_exposure,
    make_forecast,
    make_intent,
    risk_module,
)


def test_kill_switch_blocks_new_risk() -> None:
    gate = risk_module()
    gate.trip_kill_switch("manual halt", actor="tester")
    assert gate.kill.state.status is KillSwitchStatus.LATCHED
    candidate = make_candidate()
    intent = make_intent(key="killed", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )
    assert bundle.verdict.status is RiskVerdictStatus.HALT
    assert RiskRejectionReason.KILL_SWITCH in bundle.verdict.reasons
    assert bundle.kill_switch.new_order_block_status is True


def test_kill_switch_no_auto_rearm() -> None:
    gate = risk_module()
    gate.trip_kill_switch("trip", actor="tester")
    # evaluating again does not silently rearm
    candidate = make_candidate()
    intent = make_intent(key="still-dead", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert gate.kill.state.status is KillSwitchStatus.LATCHED
    assert bundle.verdict.status is RiskVerdictStatus.HALT


def test_recovery_requires_reason_and_cooldown() -> None:
    gate = risk_module()
    gate.trip_kill_switch("trip", actor="tester")
    denied = gate.recover_kill_switch("", actor="tester")
    assert denied.status is KillSwitchStatus.LATCHED
    assert denied.recovery_eligibility is RecoveryStage.INELIGIBLE
    too_soon = gate.recover_kill_switch("please", actor="tester")
    assert too_soon.status is KillSwitchStatus.LATCHED
    assert too_soon.recovery_eligibility is RecoveryStage.COOLDOWN
    gate.clock.set(AS_OF + timedelta(seconds=gate.config.recovery_cooldown_seconds + 1))
    recovered = gate.recover_kill_switch("reviewed", actor="risk-officer")
    assert recovered.status is KillSwitchStatus.ARMED
    assert recovered.recovery_eligibility is RecoveryStage.CLEARED


def test_close_only_blocks_new_risk() -> None:
    gate = risk_module()
    gate.force_mode(RiskMode.CLOSE_ONLY)
    candidate = make_candidate()
    intent = make_intent(key="close-only", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    assert bundle.risk_mode is RiskMode.CLOSE_ONLY


def test_no_new_risk_mode() -> None:
    gate = risk_module()
    gate.force_mode(RiskMode.NO_NEW_RISK)
    candidate = make_candidate()
    intent = make_intent(key="nnr", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )
    assert RiskRejectionReason.NO_NEW_RISK in bundle.verdict.reasons or bundle.verdict.status is RiskVerdictStatus.DENY


def test_symbol_scope_kill() -> None:
    gate = risk_module()
    gate.trip_kill_switch("eur", scope=KillSwitchScope.SYMBOL, scope_id="EURUSD", actor="tester")
    blocked = admitted_bundle(gate, key="eur-block")
    assert blocked.verdict.status is RiskVerdictStatus.HALT
    candidate = make_candidate(symbol="USDJPY")
    intent = make_intent(
        key="jpy-ok",
        symbol="USDJPY",
        candidate_id=candidate.candidate_id,
        entry="150.000",
        stop="149.960",
    )
    forecast = make_forecast(intent, q05="149.600", q95="150.400")
    other = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("150.000"),
        session="london",
    )
    # USDJPY is outside symbol scope; may still deny on other controls but not kill
    assert RiskRejectionReason.KILL_SWITCH not in other.verdict.reasons


def test_governance_inventory_and_audit_trail() -> None:
    gate = risk_module()
    admitted_bundle(gate, key="gov")
    snap = gate.inventory.snapshot()
    assert snap["durable"] is False
    assert any(c["id"] == "kill_switch" for c in snap["controls"])
    assert gate.audit.entries
    assert any(e.event_type in {EventType.RISK, EventType.HALT, EventType.ALERT} for e in gate.audit.entries)
    gate.inventory.note_review(AS_OF, "risk-officer", "quarterly")
    assert snap["algorithms"][0]["owner"] == "risk-function"


def test_in_memory_state_is_not_durable() -> None:
    gate = risk_module()
    assert gate.state.uri.startswith("memory://")
    assert gate.incidents.uri.startswith("memory://")
    assert gate.inventory.uri.startswith("memory://")
