from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import CommittedJournalRecord, IntegrityReport, IntegrityState
from botmoduleproject1.modules.pm7_persistence.config.defaults import GENESIS_HASH
from botmoduleproject1.modules.pm7_persistence.integrity.hash_chain import next_hash
from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


def verify_chain(records: list[CommittedJournalRecord], *, now) -> IntegrityReport:
    if not records:
        return IntegrityReport(
            occurred_at=now,
            state=IntegrityState.UNKNOWN,
            records_checked=0,
            chain_valid=True,
            genesis_hash=GENESIS_HASH,
            tip_hash=None,
        )
    mismatches: list[str] = []
    prev = GENESIS_HASH
    for rec in records:
        expected_prev = prev
        payload = rec.event.model_dump(mode="python")
        expected = next_hash(expected_prev, payload)
        if rec.previous_hash != expected_prev:
            mismatches.append(f"seq={rec.sequence} previous_hash mismatch")
        if rec.content_hash != expected:
            mismatches.append(f"seq={rec.sequence} content_hash mismatch")
        prev = rec.content_hash
    state = IntegrityState.VALID if not mismatches else IntegrityState.COMPROMISED
    return IntegrityReport(
        occurred_at=now,
        state=state,
        records_checked=len(records),
        chain_valid=not mismatches,
        mismatch_details=tuple(mismatches),
        genesis_hash=GENESIS_HASH,
        tip_hash=records[-1].content_hash,
    )
