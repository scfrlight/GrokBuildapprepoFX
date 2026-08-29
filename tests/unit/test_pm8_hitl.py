from datetime import timedelta

from botmoduleproject1.contracts.v1.alerts import ApprovalStatus
from botmoduleproject1.contracts.v1.operator import CommandDisposition
from botmoduleproject1.contracts.v1.roles import OperatorRole
from botmoduleproject1.modules.pm8_operator.config.schema import Pm8OperatorConfig
from tests.unit.pm5_support import Clock
from tests.unit.pm8_support import AS_OF, actor, pm8_module


def test_approve_does_not_emit_order():
    mod = pm8_module()
    opened = mod.handle_text("/approve", actor())
    assert opened.disposition is CommandDisposition.PENDING_HITL
    request_id = opened.details["request_id"]
    decided = mod.handle_text(f"/approve {request_id}", actor(), idempotency_key="ap2")
    assert decided.disposition is CommandDisposition.ACCEPTED
    assert decided.reason_code == "hitl_approved_not_an_order"
    assert decided.skips_pm4 is False
    assert decided.creates_order is False
    assert decided.details["order_emitted"] is False


def test_hitl_expiry():
    clock = Clock()
    mod = pm8_module(clock=clock, config=Pm8OperatorConfig(approval_ttl_seconds=30))
    opened = mod.handle_text("/approve", actor())
    request_id = opened.details["request_id"]
    clock.set(AS_OF + timedelta(seconds=31))
    decided = mod.handle_text(f"/approve {request_id}", actor(), idempotency_key="late")
    assert decided.disposition is CommandDisposition.EXPIRED


def test_operator_cannot_approve():
    mod = pm8_module()
    r = mod.handle_text("/approve", actor(OperatorRole.OPERATOR, "op"))
    assert r.disposition is CommandDisposition.UNAUTHORIZED


def test_dual_control_halt():
    mod = pm8_module(config=Pm8OperatorConfig(halt_requires_dual_control=True))
    first = mod.handle_text("/halt", actor(OperatorRole.ADMIN, "a1"), idempotency_key="h1")
    assert first.disposition is CommandDisposition.PENDING_DUAL_CONTROL
    same = mod.handle_text("/halt", actor(OperatorRole.ADMIN, "a1"), idempotency_key="h2")
    assert same.reason_code == "dual_control_same_actor"
    second = mod.handle_text("/halt", actor(OperatorRole.RISK_OFFICER, "a2"), idempotency_key="h3")
    assert second.disposition is CommandDisposition.ACCEPTED
    assert mod.halt_state.value == "halted"
