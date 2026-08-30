"""PostgreSQL store implementing the SqliteStore method surface.

NUMERIC money, TIMESTAMPTZ, JSONB payloads, append-only triggers,
unique idempotency, FOR UPDATE SKIP LOCKED outbox claiming.
Fails closed: constructor never returns a sqlite/memory store.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from botmoduleproject1.modules.pm8_persistence.postgres.ddl import (
    SCHEMA_PG_INDEXES,
    SCHEMA_PG_TRIGGERS,
    SCHEMA_PG_V1,
    SCHEMA_PG_V2,
    SCHEMA_PG_V2_DOWN,
    SCHEMA_PG_V3,
    split_sql,
)
from botmoduleproject1.modules.pm8_persistence.postgres.dsn import redact_dsn, validate_postgres_dsn
from botmoduleproject1.modules.pm8_persistence.postgres.pool import connect as pg_connect
from botmoduleproject1.modules.pm8_persistence.store import StorageUnavailable, _hash_row


def _now() -> str:
    from botmoduleproject1.contracts.v1.time import utc_now

    return utc_now().isoformat()


def _to_sql(sql: str) -> str:
    return sql.replace("?", "%s")


def _json_in(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def _cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    if isinstance(value, list):
        return json.dumps(value, default=str)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, memoryview):
        return bytes(value)
    return value


def _row(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    mapping = dict(row)
    return {str(k): _cell(v) for k, v in mapping.items()}


class PostgresStore:
    """Single transactional connection. Extra connections only for concurrent claim tests."""

    backend_identity = "postgresql"

    def __init__(
        self,
        dsn: str,
        *,
        connect_timeout: int = 5,
        statement_timeout_ms: int = 30_000,
        pool_min: int = 1,
        pool_max: int = 8,
        sslmode: str = "prefer",
        schema_name: str = "public",
        application_name: str = "pm8_persistence",
    ) -> None:
        try:
            self.dsn = validate_postgres_dsn(dsn)
        except ValueError as exc:
            raise StorageUnavailable(str(exc)) from exc
        self.path = redact_dsn(self.dsn)
        self.schema_name = schema_name or "public"
        self.connect_timeout = int(connect_timeout)
        self.statement_timeout_ms = int(statement_timeout_ms)
        self.pool_min = int(pool_min)
        self.pool_max = max(int(pool_max), 1)
        self.sslmode = sslmode
        self.application_name = application_name
        self._in_tx = False
        self._extras: list[Any] = []
        try:
            self.conn = self._open()
            self.conn.execute("SELECT 1")
        except Exception as exc:
            raise StorageUnavailable(
                f"postgresql configured but unavailable ({self.path}): {exc}"
            ) from exc
        self.bootstrap_schema()

    def _open(self) -> Any:
        conn = pg_connect(
            self.dsn,
            connect_timeout=self.connect_timeout,
            statement_timeout_ms=self.statement_timeout_ms,
            application_name=self.application_name,
        )
        if self.schema_name and self.schema_name != "public":
            ident = self.schema_name.replace('"', "")
            conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{ident}"')
            conn.execute(f'SET search_path TO "{ident}", public')
        return conn

    def new_connection(self) -> Any:
        if len(self._extras) + 1 >= self.pool_max:
            raise StorageUnavailable("postgresql connection pool exhausted")
        conn = self._open()
        self._extras.append(conn)
        return conn

    def bootstrap_schema(self) -> None:
        self._exec_script(SCHEMA_PG_V1)
        self._exec_script(SCHEMA_PG_V3)
        self._exec_script(SCHEMA_PG_INDEXES)
        self._exec_script(SCHEMA_PG_TRIGGERS)
        if self.current_version() < 1:
            self.record(1, "sequence09_consolidation", sha256(SCHEMA_PG_V1.encode()).hexdigest(), _now(), "up")

    def _exec_script(self, script: str) -> None:
        for stmt in split_sql(script):
            self.conn.execute(stmt)

    def begin(self) -> None:
        if not self._in_tx:
            self.conn.execute("BEGIN")
            self._in_tx = True

    def commit(self) -> None:
        if self._in_tx:
            self.conn.execute("COMMIT")
            self._in_tx = False

    def rollback(self) -> None:
        if self._in_tx:
            self.conn.execute("ROLLBACK")
            self._in_tx = False

    def _exec(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        return self.conn.execute(_to_sql(sql), params)

    def ping(self) -> bool:
        try:
            cur = self.conn.execute("SELECT 1 AS ok")
            row = cur.fetchone()
            return bool(row and int(row["ok"]) == 1)
        except Exception:
            return False

    def append_event(self, row: dict[str, Any]) -> int:
        prev = self.last_hash()
        payload = _json_in(row["payload_json"]) or "{}"
        row_hash = _hash_row(prev, payload + row["event_id"])
        cur = self._exec(
            """INSERT INTO events (
                event_id, correlation_id, causation_id, idempotency_key, occurred_at,
                event_type, producer, family, payload_json, prev_hash, row_hash
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
            RETURNING sequence_no""",
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
        return int(cur.fetchone()["sequence_no"])

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM events WHERE event_id=%s", (event_id,))
        return _row(cur.fetchone())

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM events ORDER BY sequence_no ASC LIMIT %s", (limit,))
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def last_hash(self) -> str:
        cur = self._exec("SELECT row_hash FROM events ORDER BY sequence_no DESC LIMIT 1")
        row = cur.fetchone()
        return str(row["row_hash"]) if row else "genesis"

    def last_sequence(self) -> int:
        cur = self._exec("SELECT COALESCE(MAX(sequence_no), 0) AS m FROM events")
        return int(cur.fetchone()["m"])

    def insert_signal(self, row: dict[str, Any]) -> None:
        self._exec(
            "INSERT INTO signals (signal_id, event_id, symbol, payload_json, committed_at) VALUES (%s,%s,%s,%s::jsonb,%s)",
            (row["signal_id"], row["event_id"], row["symbol"], _json_in(row["payload_json"]), row["committed_at"]),
        )

    def get_signal(self, signal_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM signals WHERE signal_id=%s", (signal_id,))
        return _row(cur.fetchone())

    def insert_order(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO orders (order_id, client_order_id, intent_id, verdict_id, state, payload_json, committed_at)
               VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)""",
            (
                row["order_id"],
                row["client_order_id"],
                row.get("intent_id"),
                row.get("verdict_id"),
                row["state"],
                _json_in(row["payload_json"]),
                row["committed_at"],
            ),
        )

    def get_by_client_order_id(self, client_order_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM orders WHERE client_order_id=%s", (client_order_id,))
        return _row(cur.fetchone())

    def insert_execution(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO executions (execution_id, order_id, venue_kind, venue_ticket, venue_callback_id, payload_json, committed_at)
               VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)""",
            (
                row["execution_id"],
                row["order_id"],
                row["venue_kind"],
                row.get("venue_ticket"),
                row.get("venue_callback_id"),
                _json_in(row["payload_json"]),
                row["committed_at"],
            ),
        )

    def get_by_callback(self, venue_callback_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM executions WHERE venue_callback_id=%s", (venue_callback_id,))
        return _row(cur.fetchone())

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
            """INSERT INTO idempotency_keys (edge, scope, key, result_ref, created_at, request_hash)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (edge, scope, key) DO NOTHING""",
            (edge, scope, key, result_ref, created_at, request_hash),
        )
        return cur.rowcount == 1

    def get(self, edge: str, scope: str, key: str) -> str | None:
        cur = self._exec(
            "SELECT result_ref FROM idempotency_keys WHERE edge=%s AND scope=%s AND key=%s",
            (edge, scope, key),
        )
        row = cur.fetchone()
        return str(row["result_ref"]) if row else None

    def get_idempotency(self, edge: str, scope: str, key: str) -> dict[str, Any] | None:
        cur = self._exec(
            "SELECT * FROM idempotency_keys WHERE edge=%s AND scope=%s AND key=%s",
            (edge, scope, key),
        )
        return _row(cur.fetchone())

    def enqueue(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO outbox (
                outbox_id, event_id, topic, payload_json, state, attempts, created_at, published_at,
                aggregate_id, correlation_id, causation_id, payload_version, claimed_by, claimed_until,
                next_attempt_at, failure_reason
            ) VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                row["outbox_id"],
                row["event_id"],
                row["topic"],
                _json_in(row["payload_json"]),
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
            "SELECT * FROM outbox WHERE state='pending' ORDER BY created_at ASC LIMIT %s",
            (limit,),
        )
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def claimable_outbox(self, now_iso: str, limit: int = 50) -> list[dict[str, Any]]:
        cur = self._exec(
            """SELECT * FROM outbox
               WHERE state IN ('pending','failed')
                  OR (state='claimed' AND (claimed_until IS NULL OR claimed_until < %s::timestamptz))
               ORDER BY created_at ASC LIMIT %s""",
            (now_iso, limit),
        )
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def claim_outbox(self, outbox_id: str, worker: str, until: str, now_iso: str) -> bool:
        cur = self._exec(
            """UPDATE outbox SET state='claimed', claimed_by=%s, claimed_until=%s::timestamptz
               WHERE outbox_id=%s AND (
                    state IN ('pending','failed')
                    OR (state='claimed' AND (claimed_until IS NULL OR claimed_until < %s::timestamptz))
               )""",
            (worker, until, outbox_id, now_iso),
        )
        return cur.rowcount == 1

    CLAIM_BATCH_SQL = """
WITH picked AS (
  SELECT outbox_id FROM outbox
  WHERE (
        state IN ('pending','failed')
        OR (state='claimed' AND (claimed_until IS NULL OR claimed_until < %s::timestamptz))
      )
    AND (next_attempt_at IS NULL OR next_attempt_at <= %s::timestamptz)
  ORDER BY created_at ASC
  LIMIT %s
  FOR UPDATE SKIP LOCKED
)
UPDATE outbox AS o
   SET state='claimed', claimed_by=%s, claimed_until=%s::timestamptz
  FROM picked
 WHERE o.outbox_id = picked.outbox_id
 RETURNING o.*
"""

    def claim_outbox_batch(self, worker: str, until: str, now_iso: str, limit: int = 50) -> list[dict[str, Any]]:
        cur = self.conn.execute(self.CLAIM_BATCH_SQL, (now_iso, now_iso, limit, worker, until))
        rows = [_row(x) for x in cur.fetchall()]
        return [r for r in rows if r is not None]

    def mark(self, outbox_id: str, state: str, published_at: str | None = None) -> None:
        self._exec(
            "UPDATE outbox SET state=%s, attempts=attempts+1, published_at=COALESCE(%s::timestamptz, published_at) WHERE outbox_id=%s",
            (state, published_at, outbox_id),
        )

    def mark_outbox_failed(self, outbox_id: str, reason: str, next_attempt: str, dead: bool) -> None:
        state = "dead-letter" if dead else "failed"
        self._exec(
            """UPDATE outbox SET state=%s, attempts=attempts+1, failure_reason=%s, next_attempt_at=%s::timestamptz,
               claimed_by=NULL, claimed_until=NULL WHERE outbox_id=%s""",
            (state, reason, next_attempt, outbox_id),
        )

    def get_outbox(self, outbox_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM outbox WHERE outbox_id=%s", (outbox_id,))
        return _row(cur.fetchone())

    def accept(self, event_id: str, source: str, state: str, processed_at: str) -> bool:
        cur = self._exec(
            """INSERT INTO inbox (event_id, source, state, processed_at) VALUES (%s,%s,%s,%s)
               ON CONFLICT (event_id) DO NOTHING""",
            (event_id, source, state, processed_at),
        )
        return cur.rowcount == 1

    def seen(self, event_id: str) -> bool:
        cur = self._exec("SELECT 1 AS x FROM inbox WHERE event_id=%s", (event_id,))
        return cur.fetchone() is not None

    def get_inbox(self, event_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM inbox WHERE event_id=%s", (event_id,))
        return _row(cur.fetchone())

    def mark_inbox(self, event_id: str, state: str, processed_at: str, error: str | None = None) -> None:
        self._exec(
            """UPDATE inbox SET state=%s, processed_at=%s, attempts=COALESCE(attempts,0)+1, last_error=%s
               WHERE event_id=%s""",
            (state, processed_at, error, event_id),
        )

    def insert_inbox_dead_letter(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO inbox_dead_letters
               (event_id, source, attempts, last_error, payload_json, created_at) VALUES (%s,%s,%s,%s,%s::jsonb,%s)
               ON CONFLICT (event_id) DO UPDATE SET
                 attempts=EXCLUDED.attempts, last_error=EXCLUDED.last_error,
                 payload_json=EXCLUDED.payload_json, created_at=EXCLUDED.created_at""",
            (
                row["event_id"],
                row["source"],
                row["attempts"],
                row["last_error"],
                _json_in(row.get("payload_json", "{}")),
                row["created_at"],
            ),
        )

    def save_checkpoint(self, row: dict[str, Any]) -> None:
        cursor = int(row["cursor_seq"])
        cur = self._exec("SELECT COALESCE(MAX(cursor_seq), -1) AS m FROM recovery_checkpoints")
        max_seq = int(cur.fetchone()["m"])
        if cursor < max_seq:
            raise ValueError(
                f"checkpoint cursor_seq must be monotonic non-decreasing "
                f"(got {cursor} < max {max_seq})"
            )
        self._exec(
            "INSERT INTO recovery_checkpoints (checkpoint_id, cursor_seq, payload_json, created_at) VALUES (%s,%s,%s::jsonb,%s)",
            (row["checkpoint_id"], row["cursor_seq"], _json_in(row["payload_json"]), row["created_at"]),
        )

    def latest_checkpoint(self) -> dict[str, Any] | None:
        cur = self._exec(
            "SELECT * FROM recovery_checkpoints ORDER BY cursor_seq DESC, created_at DESC LIMIT 1"
        )
        return _row(cur.fetchone())

    def upsert(self, name: str, last_event_seq: int, payload_json: str, rebuilt_at: str) -> None:
        self._exec(
            """INSERT INTO projections (name, last_event_seq, payload_json, rebuilt_at) VALUES (%s,%s,%s::jsonb,%s)
               ON CONFLICT (name) DO UPDATE SET last_event_seq=EXCLUDED.last_event_seq,
               payload_json=EXCLUDED.payload_json, rebuilt_at=EXCLUDED.rebuilt_at""",
            (name, last_event_seq, _json_in(payload_json), rebuilt_at),
        )

    def get_projection(self, name: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM projections WHERE name=%s", (name,))
        return _row(cur.fetchone())

    def upsert_named_row(self, projection: str, row_key: str, payload_json: str, source_seq: int, updated_at: str) -> None:
        self._exec(
            """INSERT INTO named_projection_rows (projection, row_key, payload_json, source_seq, updated_at)
               VALUES (%s,%s,%s::jsonb,%s,%s)
               ON CONFLICT (projection, row_key) DO UPDATE SET
                 payload_json=EXCLUDED.payload_json, source_seq=EXCLUDED.source_seq, updated_at=EXCLUDED.updated_at""",
            (projection, row_key, _json_in(payload_json), source_seq, updated_at),
        )

    def delete_named_row(self, projection: str, row_key: str) -> None:
        self._exec("DELETE FROM named_projection_rows WHERE projection=%s AND row_key=%s", (projection, row_key))

    def list_named_rows(self, projection: str) -> list[dict[str, Any]]:
        cur = self._exec(
            "SELECT * FROM named_projection_rows WHERE projection=%s ORDER BY source_seq ASC",
            (projection,),
        )
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def clear_named_projection(self, projection: str) -> None:
        self._exec("DELETE FROM named_projection_rows WHERE projection=%s", (projection,))
        self._exec("DELETE FROM processed_events WHERE projection_name=%s", (projection,))

    def set_named_meta(self, name: str, version: int, last_event_seq: int, rebuilt_at: str, status: str, lag_seq: int) -> None:
        self._exec(
            """INSERT INTO named_projection_meta (name, version, last_event_seq, rebuilt_at, status, lag_seq)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (name) DO UPDATE SET version=EXCLUDED.version, last_event_seq=EXCLUDED.last_event_seq,
               rebuilt_at=EXCLUDED.rebuilt_at, status=EXCLUDED.status, lag_seq=EXCLUDED.lag_seq""",
            (name, version, last_event_seq, rebuilt_at, status, lag_seq),
        )

    def get_named_meta(self, name: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM named_projection_meta WHERE name=%s", (name,))
        return _row(cur.fetchone())

    def mark_processed_event(self, projection_name: str, event_id: str, source_seq: int, applied_at: str) -> bool:
        cur = self._exec(
            """INSERT INTO processed_events (projection_name, event_id, source_seq, applied_at)
               VALUES (%s,%s,%s,%s)
               ON CONFLICT (projection_name, event_id) DO NOTHING""",
            (projection_name, event_id, source_seq, applied_at),
        )
        return cur.rowcount == 1

    def processed_event(self, projection_name: str, event_id: str) -> bool:
        cur = self._exec(
            "SELECT 1 AS x FROM processed_events WHERE projection_name=%s AND event_id=%s",
            (projection_name, event_id),
        )
        return cur.fetchone() is not None

    def insert_recon_run(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO reconciliation_runs
               (run_id, state, venue_available, started_at, updated_at, closed_at, payload_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                row["run_id"],
                row["state"],
                1 if row.get("venue_available") else 0,
                row["started_at"],
                row["updated_at"],
                row.get("closed_at"),
                _json_in(row["payload_json"]),
            ),
        )

    def update_recon_run(self, run_id: str, state: str, updated_at: str, closed_at: str | None = None) -> None:
        self._exec(
            "UPDATE reconciliation_runs SET state=%s, updated_at=%s, closed_at=COALESCE(%s::timestamptz, closed_at) WHERE run_id=%s",
            (state, updated_at, closed_at, run_id),
        )

    def get_recon_run(self, run_id: str) -> dict[str, Any] | None:
        return _row(self._exec("SELECT * FROM reconciliation_runs WHERE run_id=%s", (run_id,)).fetchone())

    def insert_recon_item(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO reconciliation_items
               (item_id, run_id, local_ref, venue_ref, classification, severity, state, payload_json, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)""",
            (
                row["item_id"],
                row["run_id"],
                row["local_ref"],
                row.get("venue_ref"),
                row["classification"],
                row["severity"],
                row["state"],
                _json_in(row["payload_json"]),
                row["created_at"],
            ),
        )

    def list_recon_items(self, run_id: str) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM reconciliation_items WHERE run_id=%s", (run_id,))
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def insert_mismatch_action(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO mismatch_actions
               (action_id, item_id, run_id, action, actor, occurred_at, payload_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                row["action_id"],
                row["item_id"],
                row["run_id"],
                row["action"],
                row["actor"],
                row["occurred_at"],
                _json_in(row["payload_json"]),
            ),
        )

    def insert_money(self, row: dict[str, Any]) -> None:
        self._exec(
            """INSERT INTO money_records
               (record_id, family, field, amount_canonical, scale, currency, source_event_id, committed_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
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
                "INSERT INTO recon_records (recon_id, local_ref, venue_ref, state, detail_json, committed_at) VALUES (%s,%s,%s,%s,%s::jsonb,%s)",
                (
                    row["recon_id"],
                    row["local_ref"],
                    row.get("venue_ref"),
                    row["state"],
                    _json_in(row["detail_json"]),
                    row["committed_at"],
                ),
            )
            return
        if table == "audit_log":
            self._exec(
                "INSERT INTO audit_log (audit_id, actor, action, target, payload_json, occurred_at) VALUES (%s,%s,%s,%s,%s::jsonb,%s)",
                (row["audit_id"], row["actor"], row["action"], row["target"], _json_in(row["payload_json"]), row["occurred_at"]),
            )
            return
        if table == "integrity_log":
            self._exec(
                "INSERT INTO integrity_log (check_id, state, detail_json, occurred_at) VALUES (%s,%s,%s::jsonb,%s)",
                (row["check_id"], row["state"], _json_in(row["detail_json"]), row["occurred_at"]),
            )
            return
        if table == "repair_log":
            self._exec(
                "INSERT INTO repair_log (repair_id, check_id, action, new_event_id, detail_json, occurred_at) VALUES (%s,%s,%s,%s,%s::jsonb,%s)",
                (
                    row["repair_id"],
                    row.get("check_id"),
                    row["action"],
                    row.get("new_event_id"),
                    _json_in(row["detail_json"]),
                    row["occurred_at"],
                ),
            )
            return
        if table == "snapshots":
            self._exec(
                "INSERT INTO snapshots (snapshot_id, scope, checksum, payload_json, created_at) VALUES (%s,%s,%s,%s::jsonb,%s)",
                (row["snapshot_id"], row["scope"], row["checksum"], _json_in(row["payload_json"]), row["created_at"]),
            )
            return
        if table == "backup_manifest":
            self._exec(
                "INSERT INTO backup_manifest (backup_id, path, checksum, event_count, verified, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
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
                "INSERT INTO export_packages (export_id, checksum, payload_json, created_at) VALUES (%s,%s,%s::jsonb,%s)",
                (row["export_id"], row["checksum"], _json_in(row["payload_json"]), row["created_at"]),
            )
            return
        if table == "restore_applies":
            self._exec(
                """INSERT INTO restore_applies
                   (apply_id, backup_id, target_path, stage, checksum_ok, schema_ok, mutated, trading_blocked, detail_json, occurred_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)""",
                (
                    row["apply_id"],
                    row["backup_id"],
                    row["target_path"],
                    row["stage"],
                    1 if row.get("checksum_ok") else 0,
                    1 if row.get("schema_ok") else 0,
                    1 if row.get("mutated") else 0,
                    1 if row.get("trading_blocked", True) else 0,
                    _json_in(row.get("detail_json", "{}")),
                    row["occurred_at"],
                ),
            )
            return
        raise ValueError(f"unknown insert table {table}")

    def list_open(self) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM recon_records WHERE state IN ('degraded','unavailable','mismatch')")
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def latest(self) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM snapshots ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return _row(row)
        cur = self._exec("SELECT * FROM integrity_log ORDER BY occurred_at DESC LIMIT 1")
        return _row(cur.fetchone())

    def latest_integrity(self) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM integrity_log ORDER BY occurred_at DESC LIMIT 1")
        return _row(cur.fetchone())

    def get_backup(self, backup_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM backup_manifest WHERE backup_id=%s", (backup_id,))
        return _row(cur.fetchone())

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        cur = self._exec("SELECT * FROM backup_manifest ORDER BY created_at DESC LIMIT %s", (limit,))
        return [r for r in (_row(x) for x in cur.fetchall()) if r is not None]

    def current_version(self) -> int:
        try:
            cur = self._exec(
                "SELECT version, direction FROM schema_migrations ORDER BY applied_at DESC, version DESC LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return 0
            ver = int(row["version"])
            if str(row["direction"]) == "down":
                return max(ver - 1, 0)
            return ver
        except psycopg.Error:
            return 0

    def record(self, version: int, name: str, checksum: str, applied_at: str, direction: str) -> None:
        self._exec(
            """INSERT INTO schema_migrations (version, name, checksum, applied_at, direction)
               VALUES (%s,%s,%s,%s,%s)
               ON CONFLICT (version) DO UPDATE SET
                 name=EXCLUDED.name, checksum=EXCLUDED.checksum,
                 applied_at=EXCLUDED.applied_at, direction=EXCLUDED.direction""",
            (version, name, checksum, applied_at, direction),
        )

    def get_export(self, export_id: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM export_packages WHERE export_id=%s", (export_id,))
        return _row(cur.fetchone())

    def upsert_position(self, symbol: str, qty: str, avg_px: str, as_of: str, source_seq: int) -> None:
        self._exec(
            """INSERT INTO positions_proj (symbol, qty, avg_px, as_of, source_seq) VALUES (%s,%s,%s,%s,%s)
               ON CONFLICT (symbol) DO UPDATE SET qty=EXCLUDED.qty, avg_px=EXCLUDED.avg_px,
               as_of=EXCLUDED.as_of, source_seq=EXCLUDED.source_seq""",
            (symbol, qty, avg_px, as_of, source_seq),
        )

    def get_position(self, symbol: str) -> dict[str, Any] | None:
        cur = self._exec("SELECT * FROM positions_proj WHERE symbol=%s", (symbol,))
        return _row(cur.fetchone())

    def upsert_named(self, *args: Any, **kwargs: Any) -> None:
        if len(args) == 5:
            self.upsert_position(*args)
        else:
            self.upsert(*args)

    def apply_v2(self) -> None:
        self._exec_script(SCHEMA_PG_V2)

    def revert_v2(self) -> None:
        self._exec_script(SCHEMA_PG_V2_DOWN)

    def dump_events_json(self) -> str:
        events = self.list_events(limit=1_000_000)
        return json.dumps(events, sort_keys=True)

    def truncate_all(self) -> None:
        """Test helper. TRUNCATE is not blocked by append-only DELETE triggers."""
        tables = (
            "mismatch_actions, reconciliation_items, reconciliation_runs, inbox_dead_letters, "
            "processed_events, named_projection_rows, named_projection_meta, money_records, "
            "restore_applies, restore_verifications, restart_drills, backup_schedules, "
            "export_packages, backup_manifest, snapshots, repair_log, integrity_log, audit_log, "
            "recon_records, projections, recovery_checkpoints, inbox, outbox, idempotency_keys, "
            "positions_proj, executions, orders, signals, events"
        )
        self.conn.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")

    def server_version(self) -> str:
        cur = self.conn.execute("SHOW server_version")
        return str(cur.fetchone()["server_version"])

    def diagnostics(self) -> dict[str, Any]:
        return {
            "backend": self.backend_identity,
            "path": self.path,
            "schema_version": self.current_version(),
            "event_count": self.last_sequence(),
            "memory": False,
            "sqlite_fallback": False,
            "schema_name": self.schema_name,
            "sslmode": self.sslmode,
            "pool_max": self.pool_max,
            "server_version": self.server_version() if self.ping() else None,
            "ping": self.ping(),
        }

    def close(self) -> None:
        try:
            if self._in_tx:
                self.rollback()
        except Exception:
            pass
        for extra in self._extras:
            try:
                extra.close()
            except Exception:
                pass
        self._extras.clear()
        try:
            self.conn.close()
        except Exception:
            pass


def new_id() -> str:
    return str(uuid4())
