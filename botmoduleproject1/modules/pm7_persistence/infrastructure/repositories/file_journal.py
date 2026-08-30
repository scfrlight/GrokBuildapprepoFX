from __future__ import annotations

import json
from pathlib import Path

from botmoduleproject1.contracts.v1.persistence import CommittedJournalRecord, EvidenceBundle, SnapshotRecord
from botmoduleproject1.modules.pm7_persistence.integrity.canonicalization import canonical_dumps
from botmoduleproject1.modules.pm7_persistence.journal.append_only import AppendOnlyJournal
from botmoduleproject1.modules.pm7_persistence.journal.idempotency import payload_fingerprint


class FileJournal(AppendOnlyJournal):
    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self._reload()

    def _reload(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = CommittedJournalRecord.model_validate(json.loads(line))
            self._records.append(rec)
            eid = str(rec.event.event_id)
            self._by_id[eid] = rec
            self._fingerprints[eid] = payload_fingerprint(rec.event)
            if rec.event.idempotency_key:
                self._by_idem[rec.event.idempotency_key] = rec

    def append(self, event, *, now, durable: bool = True):
        result = super().append(event, now=now, durable=durable)
        if result.disposition.value == "committed":
            rec = self.get(event.event_id)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(canonical_dumps(rec.model_dump(mode="python")) + "\n")
        return result

    def persist_snapshot(self, snap: SnapshotRecord) -> None:
        path = self.path.with_suffix(".snapshots.jsonl")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_dumps(snap.model_dump(mode="python")) + "\n")

    def load_snapshots(self) -> list[SnapshotRecord]:
        path = self.path.with_suffix(".snapshots.jsonl")
        if not path.exists():
            return []
        return [
            SnapshotRecord.model_validate(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def persist_evidence(self, bundle: EvidenceBundle) -> None:
        path = self.path.with_suffix(".evidence.jsonl")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_dumps(bundle.model_dump(mode="python")) + "\n")

    def load_evidence(self) -> list[EvidenceBundle]:
        path = self.path.with_suffix(".evidence.jsonl")
        if not path.exists():
            return []
        return [
            EvidenceBundle.model_validate(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
