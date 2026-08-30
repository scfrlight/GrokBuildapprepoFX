"""PM7/PM8 durability remediation tests. Not Sequence 15."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.contracts.v1.pm8_persistence import ApiDisposition, TableFamily
from botmoduleproject1.modules.pm7_persistence.config.schema import Pm7PersistenceConfig
from botmoduleproject1.modules.pm8_persistence.api.v1 import (
    IdempotencyConflict,
    PersistenceApiError,
    PersistenceApiV1,
    UnsupportedApiVersion,
)
from botmoduleproject1.modules.pm8_persistence.money import MoneyError, canonical, decimal_from
from botmoduleproject1.modules.pm8_persistence.outbox import InProcessPublisher
from botmoduleproject1.modules.pm8_persistence.projections import NAMED_PROJECTIONS
from botmoduleproject1.modules.pm8_persistence.restore_apply import RestoreApplyError, RestoreApplyService
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore
from tests.unit.pm7_support import make_event, pm7_module


def _api(path: Path | str) -> PersistenceApiV1:
    return PersistenceApiV1(SqliteStore(path))


def test_file_backed_sqlite_survives_process_restart(tmp_path: Path):
    db = tmp_path / "ledger.sqlite"
    api = _api(db)
    api.ingest_event(
        event_type="t",
        producer="remediation",
        family=TableFamily.EVENT,
        payload={"n": 1},
        idempotency_key="restart-1",
    )
    api.persist_order("co-restart", {"state": "accepted", "qty": "1.5", "price": "1.10000"})
    api.audit("ops", "note", "restart", {"k": 1})
    api.checkpoint()
    seq = api.store.last_sequence()
    digest = api.store.last_hash()
    pending = len(api.store.pending())
    ck = api.latest_checkpoint()
    api.store.close()

    api2 = _api(db)
    assert api2.store.last_sequence() == seq
    assert api2.store.last_hash() == digest
    assert api2.store.last_sequence() > 0
    assert api2.store.get_by_client_order_id("co-restart") is not None
    assert api2.store.list_events()[0]["payload_json"]
    assert len(api2.store.pending()) == pending
    assert api2.latest_checkpoint() is not None
    assert int(api2.latest_checkpoint()["cursor_seq"]) == int(ck["cursor_seq"])
    integrity = api2.check_integrity()
    assert integrity.state == "valid"
    api2.store.close()


def test_decimal_round_trip_and_reject_float(tmp_path: Path):
    api = _api(tmp_path / "dec.sqlite")
    assert canonical("1.10") == "1.10000000"
    assert decimal_from("1.5") == Decimal("1.50000000")
    with pytest.raises(MoneyError):
        decimal_from(float("nan"))
    with pytest.raises(MoneyError):
        api.persist_order("co-float", {"state": "accepted", "price": 1.1})
    result = api.persist_order("co-dec", {"state": "accepted", "qty": "1.25000000", "price": "1.10000000"})
    assert result.disposition is ApiDisposition.COMMITTED
    api.store.close()
    api2 = _api(tmp_path / "dec.sqlite")
    row = api2.store.get_by_client_order_id("co-dec")
    payload = __import__("json").loads(row["payload_json"])
    assert payload["qty"] == "1.25000000"
    assert payload["price"] == "1.10000000"
    assert "." in payload["qty"]
    api2.upsert_position("EURUSD", "1.25", "1.10000", "2026-08-30T00:00:00+00:00", 1)
    pos = api2.get_position("EURUSD")
    assert pos["qty"] == "1.25000000"
    api2.store.close()


def test_uow_failure_injection_rolls_back(tmp_path: Path):
    db = tmp_path / "uow.sqlite"
    for point in ("before_mutation", "before_outbox", "after_mutation", "before_audit", "before_commit"):
        api = _api(db)
        api.inject_fault = point
        with pytest.raises(RuntimeError, match="injected fault"):
            api.persist_order(f"co-{point}", {"state": "accepted", "qty": "1"})
        api.inject_fault = None
        assert api.store.get_by_client_order_id(f"co-{point}") is None
        api.store.close()
        reopened = _api(db)
        assert reopened.store.get_by_client_order_id(f"co-{point}") is None
        reopened.store.close()

    api = _api(db)
    api.inject_fault = "after_commit"
    with pytest.raises(RuntimeError, match="injected fault"):
        api.persist_order("co-committed", {"state": "accepted", "qty": "2"})
    api.inject_fault = None
    assert api.store.get_by_client_order_id("co-committed") is not None
    dup = api.persist_order("co-committed", {"state": "accepted", "qty": "2"})
    assert dup.disposition is ApiDisposition.DUPLICATE_IGNORED
    api.store.close()


def test_outbox_relay_retry_dead_letter_and_restart(tmp_path: Path):
    db = tmp_path / "ob.sqlite"
    api = _api(db)
    pub = InProcessPublisher()
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"n": 1})
    pending = api.store.pending()
    assert pending
    oid = pending[0]["outbox_id"]
    pub.fail_ids.add(oid)
    api.max_outbox_attempts = 2
    first = api.relay_outbox(publisher=pub, worker="w1")
    assert first[0]["state"] == "failed"
    second = api.relay_outbox(publisher=pub, worker="w1")
    assert second[0]["state"] == "dead-letter"
    pub.fail_ids.clear()
    api.ingest_event(event_type="t2", producer="t", family=TableFamily.EVENT, payload={"n": 2}, idempotency_key="k2")
    ok = api.relay_outbox(publisher=pub, worker="w1")
    assert any(r["state"] == "published" for r in ok)
    api.store.close()
    api2 = _api(db)
    dead = api2.store.get_outbox(oid)
    assert dead is not None
    assert dead["state"] == "dead-letter"
    api2.store.close()


def test_inbox_retry_dead_letter_and_duplicate(tmp_path: Path):
    api = _api(tmp_path / "in.sqlite")
    seen: list[str] = []
    eid = str(uuid4())

    def boom(_x: str) -> None:
        raise RuntimeError("handler down")

    api.max_outbox_attempts = 2
    first = api.consume_inbox(eid, "pm5", boom)
    assert first.disposition is ApiDisposition.REJECTED
    second = api.consume_inbox(eid, "pm5", boom)
    assert second.disposition is ApiDisposition.QUARANTINED
    ok_id = str(uuid4())
    a = api.consume_inbox(ok_id, "pm5", seen.append)
    b = api.consume_inbox(ok_id, "pm5", seen.append)
    assert a.disposition is ApiDisposition.COMMITTED
    assert b.disposition is ApiDisposition.DUPLICATE_IGNORED
    assert seen == [ok_id]


def test_named_projections_rebuild_and_duplicate(tmp_path: Path):
    api = _api(tmp_path / "proj.sqlite")
    api.persist_order("co-open", {"state": "accepted", "qty": "1", "price": "1.1"})
    api.persist_order("co-closed", {"state": "filled", "qty": "1", "price": "1.1"})
    api.persist_signal("EURUSD", {"bias": "long"}, idempotency_key="sig-1")
    api.persist_execution("co-open", "mt5_demo_sim", {"qty": "1", "avg_px": "1.10000", "symbol": "EURUSD"})
    status = api.rebuild_named_projections()
    for name in NAMED_PROJECTIONS:
        assert name in status
    opens = api.get_named_projection("open_orders")
    closed = api.get_named_projection("closed_trades")
    assert any(r["row_key"] == "co-open" for r in opens)
    assert any(r["row_key"] == "co-closed" for r in closed)
    lag = api.named_projection_status()
    assert lag["open_orders"]["lag_seq"] == 0
    again = api.rebuild_named_projections()
    assert again["open_orders"]["rows"] == status["open_orders"]["rows"]
    with pytest.raises(PersistenceApiError):
        api.get_named_projection("not-a-projection")


def test_reconciliation_run_lifecycle_and_no_silent_pass(tmp_path: Path):
    api = _api(tmp_path / "recon.sqlite")
    run = api.start_reconciliation_run(venue_available=False, actor="ops")
    with pytest.raises(PersistenceApiError, match="PASS"):
        api.add_reconciliation_item(run["run_id"], local_ref="o1", venue_ref=None, classification="pass")
    item = api.add_reconciliation_item(
        run["run_id"], local_ref="o1", venue_ref=None, classification="mismatch", severity="high"
    )
    dup = api.add_reconciliation_item(
        run["run_id"], local_ref="o1", venue_ref=None, classification="mismatch", severity="high"
    )
    assert dup["duplicate"] is True
    ack = api.acknowledge_reconciliation(run["run_id"], actor="ops", item_id=item["item_id"])
    assert ack["state"] == "acknowledged"
    api.remediate_reconciliation(run["run_id"], actor="ops", item_id=item["item_id"], correction={"note": "fix"})
    api.resolve_reconciliation(run["run_id"], actor="ops")
    closed = api.close_reconciliation(run["run_id"], actor="ops")
    assert closed["state"] == "closed"
    with pytest.raises(PersistenceApiError):
        api.add_reconciliation_item("missing", local_ref="x", venue_ref="v", classification="mismatch")


def test_isolated_restore_apply(tmp_path: Path):
    live = tmp_path / "live.sqlite"
    api = _api(live)
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"n": 9})
    before = api.store.last_sequence()
    report = api.backup(tmp_path / "bk")
    svc = RestoreApplyService(api.store)
    dry = svc.dry_run_restore(Path(report.path), report.checksum)
    assert dry["mutated"] is False
    assert api.store.last_sequence() == before
    with pytest.raises(RestoreApplyError):
        svc.verify_backup(Path(report.path), "0" * 64)
    target = svc.prepare_restore_target(tmp_path / "isolated")
    applied = svc.apply_restore(Path(report.path), report.checksum, target)
    assert applied["ok"] is True
    assert applied["trading_blocked"] is True
    assert api.store.last_sequence() == before
    restored = _api(target)
    assert restored.store.last_sequence() >= 1
    assert restored.check_integrity().state == "valid"
    restored.store.close()
    with pytest.raises(RestoreApplyError):
        svc.apply_restore(Path(report.path), report.checksum, live)
    abort = svc.restore_abort(target)
    assert abort["trading_blocked"] is True
    api.store.close()


def test_pm7_journal_and_snapshot_survive_restart(tmp_path: Path):
    cfg = Pm7PersistenceConfig(operating_mode="sqlite_local", storage_path=str(tmp_path / "pm7"))
    mod = pm7_module(config=cfg)
    first = mod.ingest(make_event(idempotency_key="pm7-r1"))
    assert first.disposition.value == "committed"
    snap = mod.capture_snapshot()
    bundle = mod.build_evidence()
    replay = mod.replay()
    assert replay.event_count == 1
    tip = mod.journal.records()[-1].content_hash
    if hasattr(mod.backend, "close"):
        mod.backend.close()
    mod2 = pm7_module(config=cfg)
    recs = mod2.journal.records()
    assert len(recs) == 1
    assert recs[0].content_hash == tip
    assert recs[0].event.idempotency_key == "pm7-r1"
    assert mod2.snapshots.items
    assert str(mod2.snapshots.items[-1].snapshot_id) == str(snap.snapshot_id)
    assert mod2.evidence.bundles
    replay2 = mod2.replay()
    assert replay2.timeline == replay.timeline
    report = mod2.verify_integrity()
    assert report.chain_valid is True
    exported = mod2.export_package()
    assert exported.checksum
    freeze = mod2.freeze(reason="legal", actor="ops")
    with pytest.raises(Exception, match="frozen"):
        mod2.purge()
    assert freeze is not None
    _ = bundle


def test_pm7_file_journal_survives_restart(tmp_path: Path):
    cfg = Pm7PersistenceConfig(operating_mode="file_backed", storage_path=str(tmp_path / "pm7f"))
    mod = pm7_module(config=cfg)
    mod.ingest(make_event(idempotency_key="file-1"))
    mod2 = pm7_module(config=cfg)
    assert len(mod2.journal.records()) == 1


def test_api_version_and_no_broker_surface():
    api = PersistenceApiV1(SqliteStore(":memory:"))
    api.require_version("v1")
    with pytest.raises(UnsupportedApiVersion):
        api.require_version("v9")
    assert not hasattr(api, "submit")
    assert not hasattr(api, "place_order")
    src = Path(__file__).resolve().parents[2] / "botmoduleproject1/modules/pm8_persistence/api/v1.py"
    text = src.read_text(encoding="utf-8")
    assert "def submit(" not in text
    assert "MetaTrader5" not in text


def test_request_idempotency_hash_conflict(tmp_path: Path):
    api = _api(tmp_path / "idem.sqlite")
    a = api.ingest_event(
        event_type="t",
        producer="t",
        family=TableFamily.EVENT,
        payload={"n": 1},
        idempotency_key="same",
    )
    assert a.disposition is ApiDisposition.COMMITTED
    b = api.ingest_event(
        event_type="t",
        producer="t",
        family=TableFamily.EVENT,
        payload={"n": 1},
        idempotency_key="same",
    )
    assert b.disposition is ApiDisposition.DUPLICATE_IGNORED
    with pytest.raises(IdempotencyConflict):
        api.ingest_event(
            event_type="t",
            producer="t",
            family=TableFamily.EVENT,
            payload={"n": 2},
            idempotency_key="same",
        )


def test_remediation_docs_exist():
    root = Path(__file__).resolve().parents[2]
    for rel in (
        "docs/PM7_PM8_REMEDIATION_PLAN.md",
        "docs/PM7_PM8A_GAP_MATRIX.md",
        "docs/guides/durable_storage.md",
        "docs/guides/decimal_financial_types.md",
        "docs/guides/unit_of_work.md",
        "docs/guides/outbox_inbox.md",
        "docs/guides/projections.md",
        "docs/guides/backup_restore.md",
        "docs/guides/pm7_replay_evidence.md",
    ):
        assert (root / rel).is_file(), rel
    matrix = (root / "docs" / "TRACEABILITY_MATRIX.md").read_text(encoding="utf-8")
    for row in ("RMD-01", "RMD-08", "RMD-11"):
        assert row in matrix
