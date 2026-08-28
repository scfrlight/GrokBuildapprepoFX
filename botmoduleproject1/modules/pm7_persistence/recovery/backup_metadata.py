from botmoduleproject1.contracts.v1.persistence import BackupMetadata, RecoveryStatus
from botmoduleproject1.modules.pm7_persistence.recovery.continuity import continuity_ok
from botmoduleproject1.modules.pm7_persistence.recovery.restore import restore_request


class RecoveryMetadataService:
    def __init__(self) -> None:
        self.status = RecoveryStatus.UNAVAILABLE
        self.reference = None
        self.last = None

    def current(self, *, now, records) -> BackupMetadata:
        if not records:
            status = RecoveryStatus.UNAVAILABLE
        elif not continuity_ok(records):
            status = RecoveryStatus.VERIFICATION_FAILED
        else:
            status = RecoveryStatus.AVAILABLE if self.reference else RecoveryStatus.UNAVAILABLE
        self.status = status
        meta = BackupMetadata(
            occurred_at=now,
            status=status,
            reference=self.reference,
            journal_sequence=records[-1].sequence if records else 0,
            checksum=records[-1].content_hash if records else None,
        )
        self.last = meta
        return meta

    def mark_stale(self, *, now, records) -> BackupMetadata:
        self.status = RecoveryStatus.STALE
        self.reference = self.reference or "stale-ref"
        meta = BackupMetadata(
            occurred_at=now,
            status=RecoveryStatus.STALE,
            reference=self.reference,
            journal_sequence=records[-1].sequence if records else 0,
            checksum=records[-1].content_hash if records else None,
            notes="stale backup metadata",
        )
        self.last = meta
        return meta

    def request_restore(self) -> RecoveryStatus:
        nxt = restore_request(current=self.status)
        self.status = nxt
        return nxt
