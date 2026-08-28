import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.persistence import IngestDisposition, JournalCategory
from botmoduleproject1.modules.pm7_persistence.domain.errors import ImmutableJournalError
from tests.unit.pm7_support import ingest_sim, make_event, pm7_module


def test_append_valid_event():
    mod = pm7_module()
    result = mod.ingest(make_event())
    assert result.disposition is IngestDisposition.COMMITTED
    assert result.sequence == 1
    assert result.content_hash


def test_immutable_committed_event():
    mod = pm7_module()
    result = mod.ingest(make_event())
    with pytest.raises(ImmutableJournalError):
        mod.mutate(result.event_id, event_payload={"x": 1})


def test_ordering():
    mod = pm7_module()
    a = mod.ingest(make_event(idempotency_key="a"))
    b = mod.ingest(make_event(idempotency_key="b", ticket="SIM-000002"))
    assert a.sequence == 1
    assert b.sequence == 2
    recs = mod.journal.records()
    assert recs[0].content_hash == recs[1].previous_hash


def test_duplicate_idempotency():
    mod = pm7_module()
    ev = make_event(idempotency_key="dup")
    first = mod.ingest(ev)
    second = mod.ingest(ev)
    assert first.disposition is IngestDisposition.COMMITTED
    assert second.disposition is IngestDisposition.DUPLICATE_IGNORED


def test_duplicate_payload_conflict():
    mod = pm7_module()
    ev = make_event(idempotency_key="conflict", event_payload={"n": 1})
    mod.ingest(ev)
    other = make_event(idempotency_key="conflict", event_payload={"n": 2}, ticket="SIM-000099")
    result = mod.ingest(other)
    assert result.disposition is IngestDisposition.CONTRADICTION_RECORDED
    assert len(mod.journal.records()) == 1


def test_correction_instead_of_mutation():
    mod = pm7_module()
    first = mod.ingest(make_event())
    corr = mod.correct(first.event_id, payload={"note": "fix"}, actor="ops", reason="typo")
    assert corr.disposition is IngestDisposition.COMMITTED
    rec = mod.get_journal_entry(corr.event_id)
    assert rec.event.category is JournalCategory.CORRECTION
    assert rec.event.causation_id == first.event_id
    assert rec.event.operator_id == "ops"
    assert mod.get_journal_entry(first.event_id) is not None


def test_causal_lineage():
    mod = pm7_module()
    first = mod.ingest(make_event())
    corr = mod.correct(first.event_id, payload={"n": 1}, actor="ops", reason="fix")
    rec = mod.get_journal_entry(corr.event_id)
    assert str(first.event_id) in rec.event.lineage_refs


def test_schema_version_validation():
    from botmoduleproject1.contracts.v1.persistence import LedgerEvent
    with pytest.raises(ValidationError):
        LedgerEvent.model_validate({"source_module": "pm5_execution", "event_type": "x"})


def test_quarantine_malformed_source():
    mod = pm7_module()
    result = mod.ingest(make_event(source_module="unknown_mod", ticket=None, truth_source="pm2_context"))
    assert result.disposition.value in {"quarantined", "rejected"}
    assert "unknown_source_module" in result.reasons


def test_source_module_validation():
    mod = pm7_module()
    result = mod.ingest(make_event(source_module="adapters.mt5", ticket=None, truth_source="unknown"))
    assert result.disposition.value in {"quarantined", "rejected"}
