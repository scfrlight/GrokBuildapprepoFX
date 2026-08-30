"""In-memory and SQLite store implementing all 19 Sequence 09 protocols.

File-backed paths survive process restart. `:memory:` is test-only.
Empty-file first start bootstraps schema; silent fallback to memory is forbidden.
"""

from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from botmoduleproject1.modules.pm8_persistence.schema.ddl import (
    SCHEMA_V1,
    SCHEMA_V2_DOWN,
    SCHEMA_V2_UP,
    SCHEMA_V3,
)


class StorageUnavailable(RuntimeError):
    pass


def _hash_row(prev: str, payload: str) -> str:
    return sha256(f"{prev}|{payload}".encode("utf-8")).hexdigest()


class SqliteStore:
    """Single connection. Business write + outbox share one IMMEDIATE transaction."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.backend_identity = "sqlite-memory" if self.path == ":memory:" else "sqlite-file"
        if self.path != ":memory:":
            parent = Path(self.path).parent
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise StorageUnavailable(f"configured storage path unavailable: {parent}") from exc
        try:
            self.conn = sqlite3.connect(self.path, isolation_level=None, timeout=30.0)
        except sqlite3.Error as exc:
            raise StorageUnavailable(f"cannot open sqlite store {self.path}") from exc
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        if self.path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
        self._in_tx = False
        self.bootstrap_schema()

    def bootstrap_schema(self) -> None:
        self.conn.executescript(SCHEMA_V1)
        self.conn.executescript(SCHEMA_V3)
        self._ensure_relay_columns()
        if self.current_version() < 1:
            self.record(1, "sequence09_consolidation", sha256(SCHEMA_V1.encode()).hexdigest(), _now(), "up")

    def _ensure_relay_columns(self) -> None:
        extras = {
            "outbox": [
                ("aggregate_id", "TEXT"),
                ("correlation_id", "TEXT"),
                ("causation_id", "TEXT"),
                ("payload_version", "TEXT"),
                ("claimed_by", "TEXT"),
                ("claimed_until", "TEXT"),
                ("next_attempt_at", "TEXT"),
                ("failure_reason", "TEXT"),
            ],
            "inbox": [
                ("attempts", "INTEGER DEFAULT 0"),
                ("request_hash", "TEXT"),
                ("payload_json", "TEXT"),
                ("last_error", "TEXT"),
            ],
            "idempotency_keys": [
                ("request_hash", "TEXT"),
            ],
        }
        for table, cols in extras.items():
            present = {r[1] for r in self._exec(f"PRAGMA table_info({table})").fetchall()}
            for name, decl in cols:
                if name not in present:
                    self._exec(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    def begin(self) -> None:
        if not self._in_tx:
            self.conn.execute("BEGIN IMMEDIATE")
            self._in_tx = True

    def commit(self) -> None:
        if self._in_tx:
            self.conn.execute("COMMIT")
            self._in_tx = False

    def rollback(self) -> None:
        if self._in_tx:
            self.conn.execute("ROLLBACK")
            self._in_tx = False

    def _exec(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def append_event(self, row: dict[str, Any]) -> int:
        prev = self.last_hash()
        payload = row["payload_json"]
        row_hash = _hash_row(prev, payload + row["event_id"])
        cur = self._exec(
            """INSERT INTO events (
                event_id, correlation_id, causation_id, idempotency_key, occurred_at,
                event_type, producer, family, payload_json, prev_hash, row_hash
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row["event_id"],
                row["correlation_id"],
                row.get("causation_id"),
                row.get("idempotency_key"),
                row["occurred_at"],
                row["event_type"],
                row["producer"],
                row["family"],
                payload,
                prev,
                row_hash,
            ),
        )
        return int(cur.lastrowid)

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM events WHERE event_id=?", (event_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM events ORDER BY sequence_no ASC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    def last_hash(self) -> str:
        cur = self._exec("SELECT row_hash FROM events ORDER BY sequence_no DESC LIMIT 1")
        row = cur.fetchone()
        return row["row_hash"] if row else "genesis"

    def last_sequence(self) -> int:
        cur = self._exec("SELECT COALESCE(MAX(sequence_no), 0) AS m FROM events")
        return int(cur.fetchone()["m"])

    def insert_signal(self, row: dict[str, Any]) -> None:
        self._exec(
            "INSERT INTO signals (signal_id, event_id, symbol, payload_json, committed_at) VALUES (?,?,?,?,?)",
            (row["signal_id"], row["event_id"], row["symbol"], row["payload_json"], row["committed_at"]),
        )

    def get_signal(self, signal_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM signals WHERE signal_id=?", (signal_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def insert_order(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO orders (order_id, client_order_id, intent_id, verdict_id, state, payload_json, committed_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                row["order_id"],
                row["client_order_id"],
                row.get("intent_id"),
                row.get("verdict_id"),
                row["state"],
                row["payload_json"],
                row["committed_at"],
            ),
        )

    def get_by_client_order_id(self, client_order_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM orders WHERE client_order_id=?", (client_order_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def insert_execution(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO executions (execution_id, order_id, venue_kind, venue_ticket, venue_callback_id, payload_json, committed_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                row["execution_id"],
                row["order_id"],
                row["venue_kind"],
                row.get("venue_ticket"),
                row.get("venue_callback_id"),
                row["payload_json"],
                row["committed_at"],
            ),
        )

    def get_by_callback(self, venue_callback_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM executions WHERE venue_callback_id=?", (venue_callback_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def put_if_absent(
        self,
        edge: str,
        scope: str,
        key: str,
        result_ref: str,
        created_at: str,
        request_hash: str = "",
    ) -> bool:
        existing = self.get_idempotency(edge, scope, key)
        if existing is not None:
            return False
        cur = self._exec(
            """INSERT OR IGNORE INTO idempotency_keys
               (edge, scope, key, result_ref, created_at, request_hash) VALUES (?,?,?,?,?,?)""",
            (edge, scope, key, result_ref, created_at, request_hash),
        )
        return cur.rowcount == 1

    def get(self, edge: str, scope: str, key: str) -> str | None:
        cur = self._exec(
            "SELECT result_ref FROM idempotency_keys WHERE edge=? AND scope=? AND key=?",
            (edge, scope, key),
        )
        row = cur.fetchone()
        return str(row["result_ref"]) if row else None

    def get_idempotency(self, edge: str, scope: str, key: str) -> dict[str, Any] | None:
        cur = self._exec(
            "SELECT * FROM idempotency_keys WHERE edge=? AND scope=? AND key=?",
            (edge, scope, key),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def enqueue(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO outbox (
                outbox_id, event_id, topic, payload_json, state, attempts, created_at, published_at,
                aggregate_id, correlation_id, causation_id, payload_version, claimed_by, claimed_until,
                next_attempt_at, failure_reason
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row["outbox_id"],
                row["event_id"],
                row["topic"],
                row["payload_json"],
                row["state"],
                row.get("attempts", 0),
                row["created_at"],
                row.get("published_at"),
                row.get("aggregate_id"),
                row.get("correlation_id"),
                row.get("causation_id"),
                row.get("payload_version", "v1"),
                row.get("claimed_by"),
                row.get("claimed_until"),
                row.get("next_attempt_at"),
                row.get("failure_reason"),
            ),
        )

    def pending(self, limit: int = 50) -> list[dict[str, Any]]:
        cur = self._exec(
            "SELECT * FROM outbox WHERE state='pending' ORDER BY created_at ASC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]

    def claimable_outbox(self, now_iso: str, limit: int = 50) -> list[dict[str, Any]]:
        cur = self._exec(
            """SELECT * FROM outbox
               WHERE state IN ('pending','failed')
                  OR (state='claimed' AND (claimed_until IS NULL OR claimed_until < ?))
               ORDER BY created_at ASC LIMIT ?""",
            (now_iso, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def claim_outbox(self, outbox_id: str, worker: str, until: str, now_iso: str) -> bool:
        cur = self._exec(
            """UPDATE outbox SET state='claimed', claimed_by=?, claimed_until=?
               WHERE outbox_id=? AND (
                    state IN ('pending','failed')
                    OR (state='claimed' AND (claimed_until IS NULL OR claimed_until < ?))
               )""",
            (worker, until, outbox_id, now_iso),
        )
        return cur.rowcount == 1

    def claim_outbox_batch(self, worker: str, until: str, now_iso: str, limit: int = 50) -> list[dict[str, Any]]:
        """SQLite local/test path. PostgreSQL uses FOR UPDATE SKIP LOCKED."""
        claimed: list[dict[str, Any]] = []
        for row in self.claimable_outbox(now_iso, limit):
            if self.claim_outbox(row["outbox_id"], worker, until, now_iso):
                item = dict(row)
                item["state"] = "claimed"
                item["claimed_by"] = worker
                item["claimed_until"] = until
                claimed.append(item)
        return claimed

    def mark(self, outbox_id: str, state: str, published_at: str | None = None) -> None:
        self._exec(
            "UPDATE outbox SET state=?, attempts=attempts+1, published_at=COALESCE(?, published_at) WHERE outbox_id=?",
            (state, published_at, outbox_id),
        )

    def mark_outbox_failed(self, outbox_id: str, reason: str, next_attempt: str, dead: bool) -> None:
        state = "dead-letter" if dead else "failed"
        self._exec(
            """UPDATE outbox SET state=?, attempts=attempts+1, failure_reason=?, next_attempt_at=?,
               claimed_by=NULL, claimed_until=NULL WHERE outbox_id=?""",
            (state, reason, next_attempt, outbox_id),
        )

    def get_outbox(self, outbox_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM outbox WHERE outbox_id=?", (outbox_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def accept(self, event_id: str, source: str, state: str, processed_at: str) -> bool:
        cur = self._exec(
            "INSERT OR IGNORE INTO inbox (event_id, source, state, processed_at) VALUES (?,?,?,?)",
            (event_id, source, state, processed_at),
        )
        return cur.rowcount == 1

    def seen(self, event_id: str) -> bool:
        cur = self._exec("SELECT 1 FROM inbox WHERE event_id=?", (event_id,))
        return cur.fetchone() is not None

    def get_inbox(self, event_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM inbox WHERE event_id=?", (event_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def mark_inbox(self, event_id: str, state: str, processed_at: str, error: str | None = None) -> None:
        self._exec(
            """UPDATE inbox SET state=?, processed_at=?, attempts=COALESCE(attempts,0)+1, last_error=?
               WHERE event_id=?""",
            (state, processed_at, error, event_id),
        )

    def insert_inbox_dead_letter(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT OR REPLACE INTO inbox_dead_letters
               (event_id, source, attempts, last_error, payload_json, created_at) VALUES (?,?,?,?,?,?)""",
            (
                row["event_id"],
                row["source"],
                row["attempts"],
                row["last_error"],
                row.get("payload_json", "{}"),
                row["created_at"],
            ),
        )

    def save_checkpoint(self, row: dict[str, Any]) -> None:
        cursor = int(row["cursor_seq"])
        cur = self._exec("SELECT COALESCE(MAX(cursor_seq), -1) FROM recovery_checkpoints")
        max_seq = int(cur.fetchone()[0])
        if cursor < max_seq:
            raise ValueError(
                f"checkpoint cursor_seq must be monotonic non-decreasing "
                f"(got {cursor} < max {max_seq})"
            )
        self._exec(
            "INSERT INTO recovery_checkpoints (checkpoint_id, cursor_seq, payload_json, created_at) VALUES (?,?,?,?)",
            (row["checkpoint_id"], row["cursor_seq"], row["payload_json"], row["created_at"]),
        )

    def latest_checkpoint(self) -> dict[str, Any] | None:
        cur = self._exec(
            "SELECT * FROM recovery_checkpoints ORDER BY cursor_seq DESC, created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def upsert(self, name: str, last_event_seq: int, payload_json: str, rebuilt_at: str) -> None:
        self._exec(
            """INSERT INTO projections (name, last_event_seq, payload_json, rebuilt_at) VALUES (?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET last_event_seq=excluded.last_event_seq,
               payload_json=excluded.payload_json, rebuilt_at=excluded.rebuilt_at""",
            (name, last_event_seq, payload_json, rebuilt_at),
        )

    def get_projection(self, name: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM projections WHERE name=?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def upsert_named_row(self, projection: str, row_key: str, payload_json: str, source_seq: int, updated_at: str) -> None:
        self._exec(
            """INSERT INTO named_projection_rows (projection, row_key, payload_json, source_seq, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(projection, row_key) DO UPDATE SET
                 payload_json=excluded.payload_json, source_seq=excluded.source_seq, updated_at=excluded.updated_at""",
            (projection, row_key, payload_json, source_seq, updated_at),
        )

    def delete_named_row(self, projection: str, row_key: str) -> None:
        self._exec("DELETE FROM named_projection_rows WHERE projection=? AND row_key=?", (projection, row_key))

    def list_named_rows(self, projection: str) -> list[dict[str, Any]]:
        cur = self._exec(
            "SELECT * FROM named_projection_rows WHERE projection=? ORDER BY source_seq ASC",
            (projection,),
        )
        return [dict(r) for r in cur.fetchall()]

    def clear_named_projection(self, projection: str) -> None:
        self._exec("DELETE FROM named_projection_rows WHERE projection=?", (projection,))
        self._exec("DELETE FROM processed_events WHERE projection_name=?", (projection,))

    def set_named_meta(self, name: str, version: int, last_event_seq: int, rebuilt_at: str, status: str, lag_seq: int) -> None:
        self._exec(
            """INSERT INTO named_projection_meta (name, version, last_event_seq, rebuilt_at, status, lag_seq)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET version=excluded.version, last_event_seq=excluded.last_event_seq,
               rebuilt_at=excluded.rebuilt_at, status=excluded.status, lag_seq=excluded.lag_seq""",
            (name, version, last_event_seq, rebuilt_at, status, lag_seq),
        )

    def get_named_meta(self, name: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM named_projection_meta WHERE name=?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def mark_processed_event(self, projection_name: str, event_id: str, source_seq: int, applied_at: str) -> bool:
        cur = self._exec(
            """INSERT OR IGNORE INTO processed_events (projection_name, event_id, source_seq, applied_at)
               VALUES (?,?,?,?)""",
            (projection_name, event_id, source_seq, applied_at),
        )
        return cur.rowcount == 1

    def processed_event(self, projection_name: str, event_id: str) -> bool:
        cur = self._exec(
            "SELECT 1 FROM processed_events WHERE projection_name=? AND event_id=?",
            (projection_name, event_id),
        )
        return cur.fetchone() is not None

    def insert_recon_run(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO reconciliation_runs
               (run_id, state, venue_available, started_at, updated_at, closed_at, payload_json)
               VALUES (?,?,?,?,?,?,?)""",
            (
                row["run_id"],
                row["state"],
                1 if row.get("venue_available") else 0,
                row["started_at"],
                row["updated_at"],
                row.get("closed_at"),
                row["payload_json"],
            ),
        )

    def update_recon_run(self, run_id: str, state: str, updated_at: str, closed_at: str | None = None) -> None:
        self._exec(
            "UPDATE reconciliation_runs SET state=?, updated_at=?, closed_at=COALESCE(?, closed_at) WHERE run_id=?",
            (state, updated_at, closed_at, run_id),
        )

    def get_recon_run(self, run_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM reconciliation_runs WHERE run_id=?", (run_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def insert_recon_item(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO reconciliation_items
               (item_id, run_id, local_ref, venue_ref, classification, severity, state, payload_json, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                row["item_id"],
                row["run_id"],
                row["local_ref"],
                row.get("venue_ref"),
                row["classification"],
                row["severity"],
                row["state"],
                row["payload_json"],
                row["created_at"],
            ),
        )

    def list_recon_items(self, run_id: str) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM reconciliation_items WHERE run_id=?", (run_id,))
        return [dict(r) for r in cur.fetchall()]

    def insert_mismatch_action(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO mismatch_actions
               (action_id, item_id, run_id, action, actor, occurred_at, payload_json)
               VALUES (?,?,?,?,?,?,?)""",
            (
                row["action_id"],
                row["item_id"],
                row["run_id"],
                row["action"],
                row["actor"],
                row["occurred_at"],
                row["payload_json"],
            ),
        )

    def insert_money(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO money_records
               (record_id, family, field, amount_canonical, scale, currency, source_event_id, committed_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                row["record_id"],
                row["family"],
                row["field"],
                row["amount_canonical"],
                row["scale"],
                row.get("currency", "QUOTE"),
                row.get("source_event_id"),
                row["committed_at"],
            ),
        )

    def insert(self, row: dict[str, Any]) -> None:
        table = row.get("_table")
        if table == "recon_records":
            self._exec(
                "INSERT INTO recon_records (recon_id, local_ref, venue_ref, state, detail_json, committed_at) VALUES (?,?,?,?,?,?)",
                (
                    row["recon_id"],
                    row["local_ref"],
                    row.get("venue_ref"),
                    row["state"],
                    row["detail_json"],
                    row["committed_at"],
                ),
            )
            return
        if table == "audit_log":
            self._exec(
                "INSERT INTO audit_log (audit_id, actor, action, target, payload_json, occurred_at) VALUES (?,?,?,?,?,?)",
                (row["audit_id"], row["actor"], row["action"], row["target"], row["payload_json"], row["occurred_at"]),
            )
            return
        if table == "integrity_log":
            self._exec(
                "INSERT INTO integrity_log (check_id, state, detail_json, occurred_at) VALUES (?,?,?,?)",
                (row["check_id"], row["state"], row["detail_json"], row["occurred_at"]),
            )
            return
        if table == "repair_log":
            self._exec(
                "INSERT INTO repair_log (repair_id, check_id, action, new_event_id, detail_json, occurred_at) VALUES (?,?,?,?,?,?)",
                (
                    row["repair_id"],
                    row.get("check_id"),
                    row["action"],
                    row.get("new_event_id"),
                    row["detail_json"],
                    row["occurred_at"],
                ),
            )
            return
        if table == "snapshots":
            self._exec(
                "INSERT INTO snapshots (snapshot_id, scope, checksum, payload_json, created_at) VALUES (?,?,?,?,?)",
                (row["snapshot_id"], row["scope"], row["checksum"], row["payload_json"], row["created_at"]),
            )
            return
        if table == "backup_manifest":
            self._exec(
                "INSERT INTO backup_manifest (backup_id, path, checksum, event_count, verified, created_at) VALUES (?,?,?,?,?,?)",
                (
                    row["backup_id"],
                    row["path"],
                    row["checksum"],
                    row["event_count"],
                    1 if row.get("verified") else 0,
                    row["created_at"],
                ),
            )
            return
        if table == "export_packages":
            self._exec(
                "INSERT INTO export_packages (export_id, checksum, payload_json, created_at) VALUES (?,?,?,?)",
                (row["export_id"], row["checksum"], row["payload_json"], row["created_at"]),
            )
            return
        raise ValueError(f"unknown insert table {table}")

    def list_open(self) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM recon_records WHERE state IN ('degraded','unavailable','mismatch')")
        return [dict(r) for r in cur.fetchall()]

    def latest(self) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM snapshots ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return dict(row)
        cur = self._exec("SELECT * FROM integrity_log ORDER BY occurred_at DESC LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None

    def latest_integrity(self) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM integrity_log ORDER BY occurred_at DESC LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None

    def get_backup(self, backup_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM backup_manifest WHERE backup_id=?", (backup_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM backup_manifest ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    def current_version(self) -> int:
        try:
            cur = self._exec(
                "SELECT version, direction FROM schema_migrations ORDER BY applied_at DESC, rowid DESC LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return 0
            ver = int(row["version"])
            if str(row["direction"]) == "down":
                return max(ver - 1, 0)
            return ver
        except sqlite3.OperationalError:
            return 0

    def record(self, version: int, name: str, checksum: str, applied_at: str, direction: str) -> None:
        self._exec(
            "INSERT OR REPLACE INTO schema_migrations (version, name, checksum, applied_at, direction) VALUES (?,?,?,?,?)",
            (version, name, checksum, applied_at, direction),
        )

    def get_export(self, export_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM export_packages WHERE export_id=?", (export_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def upsert_position(self, symbol: str, qty: str, avg_px: str, as_of: str, source_seq: int) -> None:
        self._exec(
            """INSERT INTO positions_proj (symbol, qty, avg_px, as_of, source_seq) VALUES (?,?,?,?,?)
               ON CONFLICT(symbol) DO UPDATE SET qty=excluded.qty, avg_px=excluded.avg_px,
               as_of=excluded.as_of, source_seq=excluded.source_seq""",
            (symbol, qty, avg_px, as_of, source_seq),
        )

    def get_position(self, symbol: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM positions_proj WHERE symbol=?", (symbol,))
        row = cur.fetchone()
        return dict(row) if row else None

    def upsert_named(self, *args: Any, **kwargs: Any) -> None:
        if len(args) == 5:
            self.upsert_position(*args)
        else:
            self.upsert(*args)

    def apply_v2(self) -> None:
        self.conn.executescript(SCHEMA_V2_UP)

    def revert_v2(self) -> None:
        self.conn.executescript(SCHEMA_V2_DOWN)

    def dump_events_json(self) -> str:
        events = self.list_events(limit=1_000_000)
        return json.dumps(events, sort_keys=True)

    def diagnostics(self) -> dict[str, Any]:
        return {
            "backend": self.backend_identity,
            "path": self.path,
            "schema_version": self.current_version(),
            "event_count": self.last_sequence(),
            "memory": self.path == ":memory:",
        }

    def close(self) -> None:
        self.conn.close()


def _now() -> str:
    from botmoduleproject1.contracts.v1.time import utc_now

    return utc_now().isoformat()


def new_id() -> str:
    return str(uuid4())


def open_pm8_store(
    *,
    mode: str = "memory",
    path: str | Path | None = None,
    dsn: str | None = None,
    connect_timeout: int = 5,
    statement_timeout_ms: int = 30_000,
    pool_min: int = 1,
    pool_max: int = 8,
    sslmode: str = "prefer",
    schema_name: str = "public",
) -> Any:
    """Open the configured backend. postgresql never falls back to sqlite/memory."""
    if mode == "postgresql":
        from botmoduleproject1.modules.pm8_persistence.postgres.store import PostgresStore

        if not dsn:
            raise StorageUnavailable("postgresql requires BOTMODULEPROJECT1_DATABASE_URL; sqlite fallback is forbidden")
        try:
            return PostgresStore(
                dsn,
                connect_timeout=connect_timeout,
                statement_timeout_ms=statement_timeout_ms,
                pool_min=pool_min,
                pool_max=pool_max,
                sslmode=sslmode,
                schema_name=schema_name,
            )
        except StorageUnavailable:
            raise
        except Exception as exc:
            raise StorageUnavailable(f"postgresql configured but unavailable; sqlite fallback is forbidden: {exc}") from exc
    if mode in {"disabled", "memory"}:
        return SqliteStore(":memory:")
    if not path or str(path) == ":memory:":
        raise StorageUnavailable("sqlite_local requires an explicit storage_path; memory fallback is forbidden")
    return SqliteStore(path)
