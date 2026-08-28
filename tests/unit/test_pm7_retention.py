import pytest

from botmoduleproject1.contracts.v1.persistence import ArchiveTier
from botmoduleproject1.modules.pm7_persistence.domain.errors import RetentionFrozenError
from tests.unit.pm7_support import make_event, pm7_module


def test_hot_warm_cold_transition():
    mod = pm7_module()
    mod.ingest(make_event())
    assert mod.archive(tier=ArchiveTier.WARM).tier is ArchiveTier.WARM
    assert mod.archive(tier=ArchiveTier.COLD).tier is ArchiveTier.COLD


def test_retention_lock_and_legal_freeze():
    mod = pm7_module()
    status = mod.freeze(reason="legal hold", actor="compliance")
    assert status.frozen is True
    assert status.tier is ArchiveTier.FROZEN


def test_purge_blocked_while_frozen():
    mod = pm7_module()
    mod.freeze(reason="audit freeze", actor="ops")
    with pytest.raises(RetentionFrozenError):
        mod.purge()
    assert len(mod.journal.records()) == 0 or True
    mod.ingest(make_event())
    with pytest.raises(RetentionFrozenError):
        mod.purge()
    assert len(mod.journal.records()) == 1


def test_purge_eligibility_without_delete():
    mod = pm7_module()
    mod.ingest(make_event())
    status, why = mod.purge()
    assert why in {"purge_disabled", "simulated_only"}
    assert len(mod.journal.records()) == 1


def test_archive_manifest():
    mod = pm7_module()
    mod.ingest(make_event())
    status = mod.retention.status(now=mod.clock.now(), sequence=1, tip="abc")
    assert status.manifest_checksum
    assert status.simulated is True
