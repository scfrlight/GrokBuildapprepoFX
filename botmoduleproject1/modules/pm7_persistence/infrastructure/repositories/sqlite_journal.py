from __future__ import annotations

import sqlite3
from pathlib import Path

from botmoduleproject1.modules.pm7_persistence.integrity.canonicalization import canonical_dumps
from botmoduleproject1.modules.pm7_persistence.journal.append_only import AppendOnlyJournal

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS journal (
    sequence INTEGER PRIMARY KEY,
    event_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL
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

    def schema_version(self) -> int:
        row = self._conn.execute("SELECT version FROM schema_version").fetchone()
        return int(row[0]) if row else 0

    def append(self, event, *, now, durable: bool = True):
        result = super().append(event, now=now, durable=durable)
        if result.disposition.value == "committed":
            rec = self.get(event.event_id)
            self._conn.execute(
                "INSERT INTO journal(sequence, event_id, payload, content_hash, previous_hash) VALUES (?,?,?,?,?)",
                (
                    rec.sequence,
                    str(rec.event.event_id),
                    canonical_dumps(rec.event.model_dump(mode="python")),
                    rec.content_hash,
                    rec.previous_hash,
                ),
            )
            self._conn.commit()
        return result
