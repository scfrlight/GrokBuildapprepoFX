from botmoduleproject1.contracts.v1.persistence import EvidenceState
from tests.unit.pm7_support import make_event, pm7_module


def test_build_bundle_from_source_events():
    mod = pm7_module()
    mod.ingest(make_event())
    bundle = mod.build_evidence(entity_id="ord-1", actor="ops")
    assert bundle.state is EvidenceState.ASSEMBLED
    assert bundle.source_event_ids
    assert bundle.truth_source.value == "pm5_simulation"
    assert bundle.integrity_status.value in {"valid", "unknown"}


def test_missing_event_references_flagged():
    mod = pm7_module()
    bundle = mod.build_evidence()
    assert "no_source_events" in bundle.unresolved
    assert bundle.state is EvidenceState.DRAFT


def test_incident_evidence_and_operator_action():
    mod = pm7_module()
    mod.ingest(make_event(incident_id="inc-1", category="incident", event_type="incident"))
    bundle = mod.get_incident_evidence("inc-1")
    assert bundle.entity_id == "inc-1"
    first = mod.ingest(make_event(idempotency_key="op"))
    corr = mod.correct(first.event_id, payload={"n": 1}, actor="ops", reason="review")
    rec = mod.get_journal_entry(corr.event_id)
    assert rec.event.operator_id == "ops"


def test_export_reproducibility():
    mod = pm7_module()
    mod.ingest(make_event())
    a = mod.export_package(kind="incident_evidence")
    b = mod.export_package(kind="incident_evidence")
    assert a.checksum == b.checksum
    assert a.integrity_status.value in {"valid", "unknown"}
    assert "password" not in str(a.json_payload)
