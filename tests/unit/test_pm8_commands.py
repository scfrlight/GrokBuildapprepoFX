from botmoduleproject1.contracts.v1.operator import CommandDisposition, OperatorVerb, REFUSED_VERBS
from botmoduleproject1.contracts.v1.roles import OperatorRole
from tests.unit.pm8_support import actor, pm8_module


def test_status_and_help():
    mod = pm8_module()
    r = mod.handle_text("/status", actor())
    assert r.disposition is CommandDisposition.ACCEPTED
    assert r.creates_order is False
    assert r.skips_pm4 is False
    assert "halt=" in r.message
    h = mod.handle_text("/help", actor(), idempotency_key="help-1")
    assert "Refused" in h.message


def test_observer_cannot_halt():
    mod = pm8_module()
    r = mod.handle_text("/halt", actor(OperatorRole.OBSERVER, "obs"))
    assert r.disposition is CommandDisposition.UNAUTHORIZED
    assert r.reason_code == "rbac_denied"


def test_admin_halt_is_not_broker_flatten():
    mod = pm8_module()
    r = mod.handle_text("/halt", actor())
    assert r.disposition is CommandDisposition.ACCEPTED
    assert r.reason_code == "halted"
    assert r.details["broker_flatten"] is False
    assert mod.halt_state.value == "halted"


def test_refused_order_verbs():
    mod = pm8_module()
    for text in ("/buy EURUSD", "/sell", "/order", "/resume", "/rearm", "/live", "/mt5"):
        r = mod.handle_text(text, actor(), idempotency_key=text)
        assert r.disposition is CommandDisposition.REFUSED
        assert r.verb in REFUSED_VERBS
        assert r.creates_order is False
        assert r.mt5_used is False


def test_idempotency():
    mod = pm8_module()
    a = mod.handle_text("/status", actor(), idempotency_key="same")
    b = mod.handle_text("/status", actor(), idempotency_key="same")
    assert a.disposition is CommandDisposition.ACCEPTED
    assert b.disposition is CommandDisposition.DUPLICATE


def test_ack_alert():
    mod = pm8_module()
    alert = mod.raise_alert(code="stale", message="stale feed")
    r = mod.handle_text(f"/ack {alert.alert_id}", actor(OperatorRole.OPERATOR, "op"))
    assert r.disposition is CommandDisposition.ACCEPTED
    assert alert.acked is True
