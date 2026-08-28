from botmoduleproject1.contracts.v1.post_trade import LaneKind, SeverityLevel
from tests.unit.pm6_support import observe_allow, pm6_module


def test_two_lanes_are_independent() -> None:
    pm6, _r, _p, truth = observe_allow(key="lanes")
    assert truth.operator_lane.lane is LaneKind.OPERATOR
    assert truth.control_lane.lane is LaneKind.CONTROL
    assert truth.operator_lane.headline != truth.control_lane.headline
    op = pm6.get_operator_lane()
    ctl = pm6.get_control_lane()
    assert op is not None and ctl is not None
    assert op.lane is not ctl.lane


def test_control_lane_priority_on_kill(monkeypatch=None) -> None:
    from decimal import Decimal

    from botmoduleproject1.contracts.v1.risk import KillSwitchScope
    from tests.unit.pm4_support import make_candidate, make_exposure, make_forecast, make_intent, risk_module
    from tests.unit.pm5_support import ingest_allow

    pm6 = pm6_module()
    _exe, _b, pub = ingest_allow(key="lane-kill")
    gate = risk_module()
    gate.trip_kill_switch("x", scope=KillSwitchScope.ACCOUNT)
    candidate = make_candidate()
    intent = make_intent(key="lane-kill-r", candidate_id=candidate.candidate_id)
    killed = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=make_forecast(intent),
        mid_price=Decimal("1.10000"),
        session="london",
    )
    truth = pm6.observe(pub, killed)
    assert truth.control_lane.priority is SeverityLevel.CRITICAL
    assert truth.operator_lane.priority is not None
    assert "kill=True" in truth.control_lane.items
