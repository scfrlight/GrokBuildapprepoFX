from botmoduleproject1.contracts.v1.persistence import RecoveryStatus
from tests.unit.pm7_support import make_event, pm7_module


def test_backup_metadata_unavailable_by_default():
    mod = pm7_module()
    meta = mod.backup_metadata()
    assert meta.status is RecoveryStatus.UNAVAILABLE
    assert "metadata_only" in meta.notes


def test_stale_backup_requires_review_on_restore():
    mod = pm7_module()
    mod.ingest(make_event())
    mod.recovery.mark_stale(now=mod.clock.now(), records=mod.journal.records())
    status = mod.request_restore()
    assert status is RecoveryStatus.REQUIRES_REVIEW


def test_restore_pending_when_available():
    mod = pm7_module()
    mod.ingest(make_event())
    mod.recovery.reference = "local-ref"
    meta = mod.backup_metadata()
    assert meta.status is RecoveryStatus.AVAILABLE
    assert mod.request_restore() is RecoveryStatus.RESTORE_PENDING


def test_continuity_check():
    from botmoduleproject1.modules.pm7_persistence.recovery.continuity import continuity_ok
    mod = pm7_module()
    mod.ingest(make_event())
    assert continuity_ok(mod.journal.records()) is True


def test_verification_failed_requires_review():
    from botmoduleproject1.modules.pm7_persistence.recovery.restore import restore_request
    assert restore_request(current=RecoveryStatus.VERIFICATION_FAILED) is RecoveryStatus.REQUIRES_REVIEW
