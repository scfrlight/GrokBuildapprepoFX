import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.persistence import (
    IngestDisposition,
    PersistenceTruthSource,
    ReconciliationPersistRecord,
    ReconciliationPersistState,
)
from tests.unit.pm4_support import AS_OF
from tests.unit.pm7_support import ingest_sim, make_event, pm7_module


def test_sim_ticket_stored_as_simulation():
    mod, bundle, pub, result = ingest_sim(key="truth-sim")
    rec = mod.get_journal_entry(result.event_id)
    assert rec.event.truth_source is PersistenceTruthSource.PM5_SIMULATION
    ticket = rec.event.ticket or ""
    assert ticket.startswith("SIM-") or rec.event.event_payload.get("ticket", "").startswith("SIM-") or pub.order.broker_ticket.startswith("SIM-")


def test_sim_labelled_broker_truth_rejected():
    with pytest.raises(ValidationError):
        make_event(truth_source=PersistenceTruthSource.PM5_BROKER, ticket="SIM-000001")
    mod = pm7_module()
    result = mod.ingest({
        "source_module": "pm5_execution",
        "event_type": "fill",
        "ticket": "SIM-9",
        "truth_source": "pm5_broker",
        "event_timestamp": AS_OF,
    })
    assert result.disposition is IngestDisposition.REJECTED


def test_no_venue_stays_degraded():
    mod, bundle, pub, result = ingest_sim(key="truth-recon")
    hist = mod.get_reconciliation_history()
    assert hist
    assert hist[-1].state in {ReconciliationPersistState.DEGRADED, ReconciliationPersistState.UNAVAILABLE}
    assert hist[-1].state is not ReconciliationPersistState.PASS


def test_derived_data_retains_provenance():
    mod = pm7_module()
    mod.ingest(make_event())
    report = mod.generate_report()
    assert report.lineage_refs
    assert report.dataset.truth_source.value == "derived"


def test_provenance_contradiction_recorded():
    mod = pm7_module()
    ev = make_event(idempotency_key="same")
    mod.ingest(ev)
    other = make_event(idempotency_key="same", event_payload={"other": True}, ticket="SIM-000002")
    result = mod.ingest(other)
    assert result.disposition is IngestDisposition.CONTRADICTION_RECORDED
