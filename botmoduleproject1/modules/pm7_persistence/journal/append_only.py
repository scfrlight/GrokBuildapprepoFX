from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import (
    CommittedJournalRecord,
    IngestDisposition,
    IngestResult,
    LedgerEvent,
)
from botmoduleproject1.modules.pm7_persistence.config.defaults import GENESIS_HASH
from botmoduleproject1.modules.pm7_persistence.domain.errors import ImmutableJournalError
from botmoduleproject1.modules.pm7_persistence.integrity.hash_chain import next_hash
from botmoduleproject1.modules.pm7_persistence.journal.idempotency import payload_fingerprint
from botmoduleproject1.modules.pm7_persistence.journal.sequencing import next_sequence


class AppendOnlyJournal:
    """In-memory append-only log. Optional file/sqlite backends wrap this."""

    def __init__(self) -> None:
        self._records: list[CommittedJournalRecord] = []
        self._by_id: dict[str, CommittedJournalRecord] = {}
        self._by_idem: dict[str, CommittedJournalRecord] = {}
        self._fingerprints: dict[str, str] = {}

    def __len__(self) -> int:
        return len(self._records)

    def records(self) -> list[CommittedJournalRecord]:
        return list(self._records)

    def get(self, event_id) -> CommittedJournalRecord | None:
        return self._by_id.get(str(event_id))

    def mutate(self, event_id, **_kwargs) -> None:
        raise ImmutableJournalError(f"committed record {event_id} cannot be mutated")

    def append(self, event: LedgerEvent, *, now, durable: bool = False) -> IngestResult:
        eid = str(event.event_id)
        fp = payload_fingerprint(event)
        if eid in self._by_id:
            if self._fingerprints.get(eid) == fp:
                rec = self._by_id[eid]
                return IngestResult(
                    disposition=IngestDisposition.DUPLICATE_IGNORED,
                    event_id=event.event_id,
                    sequence=rec.sequence,
                    content_hash=rec.content_hash,
                    reasons=("duplicate_event_id",),
                    truth_source=event.truth_source,
                    durable=durable,
                )
            return IngestResult(
                disposition=IngestDisposition.CONTRADICTION_RECORDED,
                event_id=event.event_id,
                reasons=("duplicate_event_id_payload_conflict",),
                truth_source=event.truth_source,
                durable=durable,
            )
        if event.idempotency_key:
            existing = self._by_idem.get(event.idempotency_key)
            if existing is not None:
                if self._fingerprints.get(str(existing.event.event_id)) == fp:
                    return IngestResult(
                        disposition=IngestDisposition.DUPLICATE_IGNORED,
                        event_id=existing.event.event_id,
                        sequence=existing.sequence,
                        content_hash=existing.content_hash,
                        reasons=("duplicate_idempotency_key",),
                        truth_source=event.truth_source,
                        durable=durable,
                    )
                return IngestResult(
                    disposition=IngestDisposition.CONTRADICTION_RECORDED,
                    event_id=existing.event.event_id,
                    reasons=("idempotency_payload_conflict",),
                    truth_source=event.truth_source,
                    durable=durable,
                )
        prev = self._records[-1].content_hash if self._records else GENESIS_HASH
        seq = next_sequence(len(self._records))
        digest = next_hash(prev, event.model_dump(mode="python"))
        stamped = event.model_copy(update={"ingested_at": event.ingested_at or now})
        record = CommittedJournalRecord(
            sequence=seq,
            event=stamped,
            content_hash=digest,
            previous_hash=prev,
            committed_at=now,
        )
        self._records.append(record)
        self._by_id[eid] = record
        self._fingerprints[eid] = fp
        if event.idempotency_key:
            self._by_idem[event.idempotency_key] = record
        return IngestResult(
            disposition=IngestDisposition.COMMITTED,
            event_id=event.event_id,
            sequence=seq,
            content_hash=digest,
            truth_source=event.truth_source,
            durable=durable,
        )
