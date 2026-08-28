from botmoduleproject1.contracts.v1.persistence import SnapshotScope, SnapshotState
from botmoduleproject1.modules.pm7_persistence.snapshot.capture import capture
from tests.unit.pm4_support import AS_OF
from tests.unit.pm7_support import make_event, pm7_module


def test_capture_and_validate_checksum():
    mod = pm7_module()
    mod.ingest(make_event())
    snap = mod.capture_snapshot()
    assert snap.state is SnapshotState.VALIDATED
    assert snap.journal_sequence == 1
    assert snap.checksum


def test_superseded_snapshot():
    mod = pm7_module()
    mod.ingest(make_event())
    first = mod.capture_snapshot()
    mod.ingest(make_event(idempotency_key="two", ticket="SIM-2"))
    second = mod.capture_snapshot()
    assert mod.snapshots.items[0].state is SnapshotState.SUPERSEDED
    assert second.journal_sequence == 2
    assert first.snapshot_id != second.snapshot_id


def test_corrupt_detection():
    snap = capture(now=AS_OF, records=[], scope=SnapshotScope.SYSTEM)
    broken = snap.model_copy(update={"checksum": "deadbeef"})
    from botmoduleproject1.modules.pm7_persistence.snapshot.validation import validate_checksum
    assert validate_checksum(broken) is SnapshotState.CORRUPT


def test_journal_sequence_linkage():
    mod = pm7_module()
    mod.ingest(make_event())
    snap = mod.capture_snapshot()
    assert snap.journal_sequence == mod.journal.records()[-1].sequence
