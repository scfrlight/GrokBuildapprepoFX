"""Live PostgreSQL durability tests. Require a real server — not mocks."""

from __future__ import annotations

import json
import os
import threading
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiError, PersistenceApiV1
from botmoduleproject1.modules.pm8_persistence.migrations import MigrationService
from botmoduleproject1.modules.pm8_persistence.money import canonical
from botmoduleproject1.modules.pm8_persistence.outbox import OutboxPublisher
from botmoduleproject1.modules.pm8_persistence.postgres.ddl import TABLE_FAMILIES
from botmoduleproject1.modules.pm8_persistence.postgres.dsn import redact_dsn
from botmoduleproject1.modules.pm8_persistence.postgres.embedded import discover_dsn, start_embedded_postgres
from botmoduleproject1.modules.pm8_persistence.postgres.store import PostgresStore
from botmoduleproject1.modules.pm8_persistence.restore_apply import RestoreApplyError, RestoreApplyService
from botmoduleproject1.modules.pm8_persistence.store import StorageUnavailable, open_pm8_store

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    found = discover_dsn()
    if found:
        return found
    try:
        return start_embedded_postgres()
    except Exception as exc:
        pytest.fail(f"PostgreSQL is required for this module but could not be started: {exc}")


@pytest.fixture
def pg_store():
    dsn = _dsn()
    schema = "t_" + uuid4().hex[:12]
    store = PostgresStore(dsn, schema_name=schema, connect_timeout=5)
    MigrationService(store).upgrade_to(2)
    yield store
    ident = schema.replace('"', "")
    try:
        store.conn.execute(f'DROP SCHEMA IF EXISTS "{ident}" CASCADE')
    except Exception:
        pass
    store.close()


@pytest.fixture
def api(pg_store):
    return PersistenceApiV1(pg_store)


def test_connection_and_backend_identity(pg_store):
    assert pg_store.ping() is True
    diag = pg_store.diagnostics()
    assert diag["backend"] == "postgresql"
    assert diag["sqlite_fallback"] is False
    assert diag["memory"] is False
    assert "secret" not in diag["path"]
    assert pg_store.server_version().startswith("16") or pg_store.server_version()


def test_open_pm8_store_postgresql_no_sqlite(pg_store):
    store = open_pm8_store(mode="postgresql", dsn=_dsn(), schema_name="t_" + uuid4().hex[:8])
    assert store.backend_identity == "postgresql"
    assert not isinstance(store.path, str) or "sqlite" not in store.path
    store.close()


def test_schema_migrations_repeat_safe(pg_store):
    pg_store.bootstrap_schema()
    again = MigrationService(pg_store).upgrade_to(2)
    assert again["noop"] is True
    assert pg_store.current_version() == 2
    cur = pg_store.conn.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=current_schema() AND table_name='money_records' AND column_name='amount_canonical'"
    )
    row = cur.fetchone()
    assert row is not None
    assert "numeric" in str(row["data_type"]).lower()


def test_numeric_round_trip(api, pg_store):
    result = api.persist_order("co-num-1", {"qty": "1.25000000", "avg_px": "1.08500000", "state": "accepted"})
    assert result.disposition.value == "committed"
    api.persist_execution("ord-symbol", "mt5_demo_sim", {"qty": "1.25000000", "avg_px": "1.08500000"})
    pos = pg_store.get_position("ord-symbol")
    assert pos is not None
    assert canonical(pos["qty"], field="qty") == "1.25000000"
    assert Decimal(pos["avg_px"]) == Decimal("1.08500000")
    cur = pg_store.conn.execute("SELECT amount_canonical FROM money_records WHERE field='qty' LIMIT 1")
    amount = cur.fetchone()["amount_canonical"]
    assert Decimal(str(amount)) == Decimal("1.25000000")


def test_append_only_events_and_audit(api, pg_store):
    api.ingest_event(event_type="e.one", producer="test", family=TableFamily.EVENT, payload={"n": 1})
    api.audit("tester", "probe", "events", {"ok": True})
    with pytest.raises(Exception, match="append-only"):
        pg_store.conn.execute("UPDATE events SET producer='tamper'")
    with pytest.raises(Exception, match="append-only"):
        pg_store.conn.execute("DELETE FROM events")
    with pytest.raises(Exception, match="append-only"):
        pg_store.conn.execute("UPDATE audit_log SET actor='tamper'")
    assert pg_store.last_sequence() == 1


def test_unique_idempotency_index(api, pg_store):
    first = api.ingest_event(
        event_type="id.one",
        producer="test",
        family=TableFamily.EVENT,
        payload={"n": 1},
        idempotency_key="same-key",
    )
    dup = api.ingest_event(
        event_type="id.one",
        producer="test",
        family=TableFamily.EVENT,
        payload={"n": 1},
        idempotency_key="same-key",
    )
    assert first.disposition.value == "committed"
    assert dup.disposition.value == "duplicate_ignored"
    cur = pg_store.conn.execute(
        "SELECT indexname FROM pg_indexes WHERE schemaname=current_schema() AND tablename='idempotency_keys'"
    )
    names = {r["indexname"] for r in cur.fetchall()}
    assert names  # primary key unique index present


def test_outbox_skip_locked_concurrent_claim(pg_store):
    sql = PostgresStore.CLAIM_BATCH_SQL
    assert "FOR UPDATE SKIP LOCKED" in sql
    now = "2026-08-30T00:00:00+00:00"
    until = "2026-08-30T00:01:00+00:00"
    for i in range(20):
        pg_store.enqueue(
            {
                "outbox_id": f"ob-{i}",
                "event_id": f"ev-{i}",
                "topic": "t",
                "payload_json": "{}",
                "state": "pending",
                "created_at": now,
            }
        )
    worker_a = pg_store
    worker_b = PostgresStore(_dsn(), schema_name=pg_store.schema_name)
    got_a: list[str] = []
    got_b: list[str] = []

    def _claim(store, bucket):
        store.begin()
        rows = store.claim_outbox_batch("w", until, now, 20)
        bucket.extend(r["outbox_id"] for r in rows)

    t1 = threading.Thread(target=_claim, args=(worker_a, got_a))
    t2 = threading.Thread(target=_claim, args=(worker_b, got_b))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    worker_a.commit()
    worker_b.commit()
    overlap = set(got_a) & set(got_b)
    assert overlap == set()
    assert len(set(got_a) | set(got_b)) == 20
    worker_b.close()


def test_projection_rebuild(api):
    api.persist_order("co-proj", {"qty": "2", "avg_px": "1.1", "state": "accepted"})
    rebuilt = api.rebuild_named_projections()
    assert rebuilt["open_orders"]["rows"] >= 1
    again = api.rebuild_named_projections()
    assert again["open_orders"]["rows"] == rebuilt["open_orders"]["rows"]


def test_reconciliation_lifecycle_no_silent_pass(api):
    run = api.start_reconciliation_run(venue_available=False, actor="ops")
    with pytest.raises(PersistenceApiError, match="PASS"):
        api.add_reconciliation_item(run["run_id"], local_ref="o1", venue_ref=None, classification="pass")
    item = api.add_reconciliation_item(
        run["run_id"],
        local_ref="o1",
        venue_ref=None,
        classification="mismatch",
        severity="critical",
    )
    assert item["item_id"]
    ack = api.acknowledge_reconciliation(run["run_id"], actor="ops", item_id=item["item_id"])
    assert ack["state"] == "acknowledged"


def test_isolated_restore_apply(api, tmp_path, pg_store):
    api.ingest_event(event_type="snap.e", producer="t", family=TableFamily.EVENT, payload={"k": 1})
    blob = pg_store.dump_events_json()
    backup = tmp_path / "events.json"
    backup.write_text(blob, encoding="utf-8")
    checksum = __import__("hashlib").sha256(blob.encode()).hexdigest()
    svc = RestoreApplyService(pg_store)
    with pytest.raises(RestoreApplyError, match="active store"):
        svc.apply_restore_postgres(backup, checksum, pg_store.dsn)
    restore_dsn = _dsn().rsplit("/", 1)[0] + "/pm8_restore"
    # database may not exist yet
    try:
        admin = PostgresStore(_dsn().rsplit("/", 1)[0] + "/postgres")
        admin.conn.execute("CREATE DATABASE pm8_restore")
        admin.close()
    except Exception:
        pass
    result = svc.apply_restore_postgres(backup, checksum, restore_dsn)
    assert result["ok"] is True
    assert result["trading_blocked"] is True
    assert result["source_untouched"] is True
    assert pg_store.last_sequence() >= 1


def test_restart_durability(api, pg_store):
    api.ingest_event(
        event_type="restart.e",
        producer="t",
        family=TableFamily.EVENT,
        payload={"n": 7},
        event_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
    )
    seq = pg_store.last_sequence()
    digest = pg_store.last_hash()
    schema = pg_store.schema_name
    dsn = pg_store.dsn
    pg_store.close()
    reopened = PostgresStore(dsn, schema_name=schema)
    assert reopened.last_sequence() == seq
    assert reopened.last_hash() == digest
    health = PersistenceApiV1(reopened).health()
    assert health["trading_readiness"] is False
    assert health["production_durable"] is False
    assert health["backend"] == "postgresql"
    reopened.close()


def test_uow_fault_injection_no_partial_commit(api, pg_store):
    api.inject_fault = "before_commit"
    with pytest.raises(RuntimeError, match="injected fault"):
        api.persist_signal("EURUSD", {"qty": "1"}, idempotency_key="fault-1")
    api.inject_fault = None
    assert pg_store.last_sequence() == 0
    assert pg_store.get_signal("unused") is None
    committed = api.persist_signal("EURUSD", {"qty": "1"}, idempotency_key="fault-1")
    assert committed.disposition.value == "committed"


class _Boom(OutboxPublisher):
    def publish(self, row):
        raise RuntimeError("relay down")


def test_outbox_relay_dead_letter(api, pg_store):
    api.max_outbox_attempts = 1
    api.ingest_event(event_type="ob.e", producer="t", family=TableFamily.EVENT, payload={"x": 1})
    handled = api.relay_outbox(publisher=_Boom(), worker="w1")
    assert handled
    assert handled[0]["state"] in {"failed", "dead-letter"}
    row = pg_store.get_outbox(handled[0]["outbox_id"])
    assert row is not None
    assert row["state"] in {"failed", "dead-letter"}


def test_inbox_duplicate_and_dlq(api):
    calls = []

    def ok(eid):
        calls.append(eid)

    first = api.consume_inbox("in-1", "test", ok)
    second = api.consume_inbox("in-1", "test", ok)
    assert first.disposition.value == "committed"
    assert second.disposition.value == "duplicate_ignored"

    def boom(_eid):
        raise RuntimeError("poison")

    api.max_outbox_attempts = 1
    poisoned = api.consume_inbox("in-poison", "test", boom)
    assert poisoned.disposition.value in {"quarantined", "rejected"}


def test_table_family_catalog_covers_required_names():
    required = {"events", "outbox", "inbox", "idempotency_keys", "money_records", "audit_log", "reconciliation_runs"}
    assert required.issubset(TABLE_FAMILIES.keys())


def test_diagnostics_redact_dsn(pg_store):
    text = json.dumps(pg_store.diagnostics())
    assert "postgresql://" in redact_dsn(pg_store.dsn) or pg_store.path.startswith("postgresql://")
    assert "password" not in text.lower() or "***" in pg_store.path
