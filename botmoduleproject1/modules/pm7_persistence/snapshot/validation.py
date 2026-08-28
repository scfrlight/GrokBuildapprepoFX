from botmoduleproject1.contracts.v1.persistence import SnapshotState
from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


def validate_checksum(record) -> SnapshotState:
    expected = sha256_hex({"sequence": record.journal_sequence, "payload": record.payload})
    if expected != record.checksum:
        return SnapshotState.CORRUPT
    return SnapshotState.VALIDATED
