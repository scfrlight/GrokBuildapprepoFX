from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import FillEvent
from botmoduleproject1.contracts.v1.post_trade import IncidentType, SeverityLevel
from botmoduleproject1.contracts.v1.risk import KillSwitchScope
from tests.unit.pm4_support import make_candidate, make_exposure, make_forecast, make_intent, risk_module
from tests.unit.pm5_support import ingest_allow
from tests.unit.pm6_support import observe_allow, pm6_module


def test_quantity_drift_detected() -> None:
    pm6 = pm6_module()
    _exe, bundle, pub = ingest_allow(key="qty-drift")
    extra = FillEvent(
        order_id=pub.order.order_id,
        occurred_at=pub.occurred_at,
        quantity=Decimal("10"),
        price=Decimal("1.1"),
        source="simulation",
        ticket=pub.order.broker_ticket,
    )
    order = pub.order.model_copy(
        update={"filled_quantity": pub.order.original_quantity + Decimal("10")}
    )
    forged = pub.model_copy(update={"order": order, "fills": pub.fills + (extra,)})
    truth = pm6.observe(forged, bundle)
    assert any(a.detector == "quantity_drift" for a in truth.alerts)
    assert any(i.incident_type is IncidentType.POST_TRADE_CONTROL_BREACH for i in truth.incidents)


def test_execution_after_kill_detected() -> None:
    pm6 = pm6_module()
    _exe, _bundle, pub = ingest_allow(key="kill-cont")
    gate = risk_module()
    gate.trip_kill_switch("latched", scope=KillSwitchScope.ACCOUNT, actor="test")
    candidate = make_candidate()
    intent = make_intent(key="kill-cont-r", candidate_id=candidate.candidate_id)
    killed = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=make_forecast(intent),
        mid_price=Decimal("1.10000"),
        session="london",
    )
    truth = pm6.observe(pub, killed)
    assert any(a.detector == "execution_after_kill" for a in truth.alerts)
    assert any(i.incident_type is IncidentType.KILL_STATE_BREACH for i in truth.incidents)
    assert any(i.severity is SeverityLevel.CRITICAL for i in truth.incidents)
    assert truth.control_lane.priority is SeverityLevel.CRITICAL


def test_unresolved_mismatch_incident() -> None:
    pm6 = pm6_module()
    _exe, bundle, pub = ingest_allow(key="mismatch")
    from botmoduleproject1.contracts.v1.execution import ReconciliationOutcome

    recon = pub.reconciliation.model_copy(
        update={
            "outcome": ReconciliationOutcome.MISMATCH,
            "broker_truth_available": True,
            "consistent": False,
        }
    )
    # keep SIM ticket so sim_as_broker also fires; use CRITICAL without broker_truth to isolate mismatch?
    # mismatch with broker_truth_available True AND SIM-* triggers provenance reject.
    # Use mismatch with broker_truth False - then it's not sim_labelled.
    recon = pub.reconciliation.model_copy(
        update={"outcome": ReconciliationOutcome.MISMATCH, "broker_truth_available": False, "consistent": False}
    )
    forged = pub.model_copy(update={"reconciliation": recon})
    truth = pm6.observe(forged, bundle)
    assert any(a.detector == "recon_mismatch" for a in truth.alerts)
    assert any(i.incident_type is IncidentType.RECONCILIATION_FOLLOWUP_REQUIRED for i in truth.incidents)
