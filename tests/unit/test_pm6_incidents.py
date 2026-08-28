import pytest

from botmoduleproject1.contracts.v1.post_trade import IncidentState
from botmoduleproject1.modules.pm6_post_trade.domain.errors import IllegalIncidentTransition
from tests.unit.pm6_support import pm6_module


def _open_critical():
    from decimal import Decimal

    from botmoduleproject1.contracts.v1.risk import KillSwitchScope
    from tests.unit.pm4_support import make_candidate, make_exposure, make_forecast, make_intent, risk_module
    from tests.unit.pm5_support import ingest_allow

    pm6 = pm6_module()
    _exe, _b, pub = ingest_allow(key="inc-life")
    gate = risk_module()
    gate.trip_kill_switch("x", scope=KillSwitchScope.ACCOUNT)
    candidate = make_candidate()
    intent = make_intent(key="inc-life-r", candidate_id=candidate.candidate_id)
    killed = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=make_forecast(intent),
        mid_price=Decimal("1.10000"),
        session="london",
    )
    truth = pm6.observe(pub, killed)
    inc = next(i for i in truth.incidents if i.incident_type.value == "kill_state_breach")
    return pm6, inc


def test_incident_lifecycle_and_no_silent_drop() -> None:
    pm6, inc = _open_critical()
    assert inc.state is IncidentState.ESCALATED
    contained = pm6.contain_incident(inc.incident_id)
    assert contained.state is IncidentState.CONTAINED
    resolved = pm6.resolve_incident(inc.incident_id)
    assert resolved.state is IncidentState.RESOLVED
    closed = pm6.close_incident(inc.incident_id, reason="reviewed")
    assert closed.state is IncidentState.CLOSED
    assert any(i.incident_id == inc.incident_id for i in pm6.list_incidents())


def test_illegal_transition_rejected() -> None:
    from botmoduleproject1.modules.pm6_post_trade.incidents.lifecycle import transit

    pm6, inc = _open_critical()
    with pytest.raises(IllegalIncidentTransition):
        transit(inc, IncidentState.CLOSED, now=pm6.clock.now())


def test_suppress_requires_reason() -> None:
    pm6, inc = _open_critical()
    with pytest.raises(ValueError):
        pm6.suppress_incident(inc.incident_id, reason="  ")
    held = pm6.suppress_incident(inc.incident_id, reason="duplicate_review")
    assert held.suppressed is True
    assert held.suppress_reason == "duplicate_review"
    assert pm6.incidents.by_id(inc.incident_id) is not None


def test_transfer_to_persistence_keeps_record() -> None:
    pm6, inc = _open_critical()
    moved = pm6.transfer_incident(inc.incident_id)
    assert moved.state is IncidentState.TRANSFERRED_TO_PERSISTENCE
    assert pm6.incidents.by_id(inc.incident_id) is not None
