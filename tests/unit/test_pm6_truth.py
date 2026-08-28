from botmoduleproject1.contracts.v1.execution import ReconciliationOutcome
from botmoduleproject1.contracts.v1.post_trade import IntakeDisposition, TruthSource
from tests.unit.pm5_support import ingest_allow
from tests.unit.pm6_support import observe_allow, pm6_module


def test_sim_ticket_is_simulation_truth() -> None:
    _pm6, _risk, pub, truth = observe_allow(key="truth-sim")
    assert pub.order.broker_ticket.startswith("SIM-")
    assert truth.truth_source is TruthSource.SIMULATION_TRUTH
    assert truth.snapshot.reconciliation_status == "degraded"


def test_sim_labelled_broker_truth_rejected() -> None:
    pm6 = pm6_module()
    _exe, bundle, pub = ingest_allow(key="truth-bad")
    recon = pub.reconciliation.model_copy(update={"broker_truth_available": True, "outcome": ReconciliationOutcome.PASS})
    forged = pub.model_copy(update={"reconciliation": recon})
    truth = pm6.observe(forged, bundle)
    assert truth.intake.disposition is IntakeDisposition.REJECTED
    assert "sim_labelled_broker_truth" in truth.intake.reasons
    assert any(i.incident_type.value == "truth_provenance_conflict" for i in truth.incidents)


def test_no_venue_stays_degraded() -> None:
    _pm6, _risk, pub, truth = observe_allow(key="truth-deg")
    assert pub.reconciliation.outcome is ReconciliationOutcome.DEGRADED
    assert pub.reconciliation.broker_truth_available is False
    assert truth.snapshot.reconciliation_status == "degraded"
    assert truth.snapshot.broker_truth_available is False
    assert truth.truth_source is not TruthSource.BROKER_TRUTH
    assert truth.truth_source is not TruthSource.RECONCILED_TRUTH
