from botmoduleproject1.contracts.v1.persistence import SnapshotRecord, SnapshotScope, SnapshotState
from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


def capture(*, now, records, scope: SnapshotScope = SnapshotScope.SYSTEM) -> SnapshotRecord:
    seq = records[-1].sequence if records else 0
    payload = {
        "count": len(records),
        "tip": records[-1].content_hash if records else None,
        "event_ids": [str(r.event.event_id) for r in records[-8:]],
    }
    checksum = sha256_hex({"sequence": seq, "payload": payload})
    return SnapshotRecord(
        occurred_at=now,
        scope=scope,
        state=SnapshotState.CAPTURED,
        journal_sequence=seq,
        checksum=checksum,
        payload=payload,
    )
