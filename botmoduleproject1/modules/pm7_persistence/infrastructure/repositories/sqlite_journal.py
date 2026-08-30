from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from botmoduleproject1.contracts.v1.persistence import CommittedJournalRecord, EvidenceBundle, SnapshotRecord
from botmoduleproject1.modules.pm7_persistence.integrity.canonicalization import canonical_dumps
from botmoduleproject1.modules.pm7_persistence.journal.append_only import AppendOnlyJournal
from botmoduleproject1.modules.pm7_persistence.journal.idempotency import payload_fingerprint

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS journal (
    sequence INTEGER PRIMARY KEY,
    event_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    journal_sequence INTEGER NOT NULL,
    checksum TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
    bundle_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL
);
"""


class SqliteJournal(AppendOnlyJournal):
    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.executescript(SCHEMA)
        cur = self._conn.execute("SELECT COUNT(*) FROM schema_version")
        if cur.fetchone()[0] == 0:
            self._conn.execute("INSERT INTO schema_version(version) VALUES (1)")
            self._conn.commit()
        self._reload()

    def schema_version(self) -> int:
        row = self._conn.execute("SELECT version FROM schema_version").fetchone()
        return int(row[0]) if row else 0

    def _reload(self) -> None:
        rows = self._conn.execute(
            "SELECT sequence, event_id, payload, content_hash, previous_hash FROM journal ORDER BY sequence ASC"
        ).fetchall()
        for sequence, event_id, payload, content_hash, previous_hash in rows:
            rec = self._record_from_payload(payload, sequence, event_id, content_hash, previous_hash)
            self._records.append(rec)
            eid = str(rec.event.event_id)
            self._by_id[eid] = rec
            self._fingerprints[eid] = payload_fingerprint(rec.event)
            if rec.event.idempotency_key:
                self._by_idem[rec.event.idempotency_key] = rec

    def _record_from_payload(self, payload: str, sequence: int, event_id: str, content_hash: str, previous_hash: str):
        data = json.loads(payload)
        if "event" in data:
            return CommittedJournalRecord.model_validate(data)
        from botmoduleproject1.contracts.v1.persistence import LedgerEvent
        from botmoduleproject1.contracts.v1.time import utc_now

        event = LedgerEvent.model_validate(data)
        return CommittedJournalRecord(
            sequence=sequence,
            event=event,
            content_hash=content_hash,
            previous_hash=previous_hash,
            committed_at=event.ingested_at or event.event_timestamp or utc_now(),
        )

    def append(self, event, *, now, durable: bool = True):
        result = super().append(event, now=now, durable=durable)
        if result.disposition.value == "committed":
            rec = self.get(event.event_id)
            self._conn.execute(
                "INSERT INTO journal(sequence, event_id, payload, content_hash, previous_hash) VALUES (?,?,?,?,?)",
                (
                    rec.sequence,
                    str(rec.event.event_id),
                    canonical_dumps(rec.model_dump(mode="python")),
                    rec.content_hash,
                    rec.previous_hash,
                ),
            )
            self._conn.commit()
        return result

    def persist_snapshot(self, snap: SnapshotRecord) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO snapshots(snapshot_id, payload, journal_sequence, checksum) VALUES (?,?,?,?)",
            (
                str(snap.snapshot_id),
                canonical_dumps(snap.model_dump(mode="python")),
                snap.journal_sequence,
                snap.checksum,
            ),
        )
        self._conn.commit()

    def load_snapshots(self) -> list[SnapshotRecord]:
        rows = self._conn.execute("SELECT payload FROM snapshots ORDER BY journal_sequence ASC").fetchall()
        return [SnapshotRecord.model_validate(json.loads(r[0])) for r in rows]

    def persist_evidence(self, bundle: EvidenceBundle) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO evidence(bundle_id, payload) VALUES (?,?)",
            (str(bundle.bundle_id), canonical_dumps(bundle.model_dump(mode="python"))),
        )
        self._conn.commit()

    def load_evidence(self) -> list[EvidenceBundle]:
        rows = self._conn.execute("SELECT payload FROM evidence").fetchall()
        return [EvidenceBundle.model_validate(json.loads(r[0])) for r in rows]

    def close(self) -> None:
        self._conn.close()
