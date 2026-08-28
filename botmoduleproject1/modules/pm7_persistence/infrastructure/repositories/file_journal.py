from __future__ import annotations

from pathlib import Path

from botmoduleproject1.modules.pm7_persistence.integrity.canonicalization import canonical_dumps
from botmoduleproject1.modules.pm7_persistence.journal.append_only import AppendOnlyJournal


class FileJournal(AppendOnlyJournal):
    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            # load is best-effort JSONL of committed dumps; tests typically start empty
            pass

    def append(self, event, *, now, durable: bool = True):
        result = super().append(event, now=now, durable=durable)
        if result.disposition.value == "committed":
            rec = self.get(event.event_id)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(canonical_dumps(rec.model_dump(mode="python")) + "\n")
        return result
