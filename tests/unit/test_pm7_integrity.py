from botmoduleproject1.contracts.v1.persistence import IntegrityState
from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex
from botmoduleproject1.modules.pm7_persistence.integrity.verification import verify_chain
from tests.unit.pm4_support import AS_OF
from tests.unit.pm7_support import make_event, pm7_module


def test_canonical_hashing_and_valid_chain():
    mod = pm7_module()
    mod.ingest(make_event(idempotency_key="h1"))
    mod.ingest(make_event(idempotency_key="h2", ticket="SIM-2"))
    report = mod.verify_integrity()
    assert report.chain_valid is True
    assert report.state is IntegrityState.VALID
    assert report.claim == "tamper_detection_only"
    assert len(sha256_hex({"a": 1})) == 64


def test_mismatch_compromised():
    mod = pm7_module()
    mod.ingest(make_event())
    recs = mod.journal.records()
    tampered = recs[0].model_copy(update={"content_hash": "00" * 32})
    report = verify_chain([tampered], now=AS_OF)
    assert report.state is IntegrityState.COMPROMISED
    assert report.mismatch_details


def test_repair_is_correction_not_rewrite():
    mod = pm7_module()
    first = mod.ingest(make_event())
    mod.correct(first.event_id, payload={"repaired": True}, actor="ops", reason="repair")
    assert len(mod.journal.records()) == 2
    assert mod.get_journal_entry(first.event_id).event.event_payload.get("ok") is True


def test_archive_checksum_on_export():
    mod = pm7_module()
    mod.ingest(make_event())
    pkg = mod.export_package()
    assert pkg.checksum
    assert pkg.manifest["checksum"] == pkg.checksum
