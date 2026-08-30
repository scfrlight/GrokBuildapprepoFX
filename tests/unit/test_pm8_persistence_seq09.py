"""Canonical Sequence 09 — PM8 consolidation build gate."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import NullStorage
from botmoduleproject1.contracts.v1.pm8_persistence import ApiDisposition, TableFamily
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1, SERVICE_CATALOG
from botmoduleproject1.modules.pm8_persistence.module import PM8PersistenceModule
from botmoduleproject1.modules.pm8_persistence.repositories.protocols import PROTOCOL_CATALOG
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def _api(tmp_path: Path | None = None) -> PersistenceApiV1:
    path = str(tmp_path / "pm8.sqlite") if tmp_path else ":memory:"
    return PersistenceApiV1(SqliteStore(path))


def test_protocol_and_service_minimums():
    assert len(PROTOCOL_CATALOG) >= 19
    assert len(SERVICE_CATALOG) >= 20


def test_append_only_and_dedupe(tmp_path: Path):
    api = _api(tmp_path)
    eid = str(uuid4())
    a = api.ingest_event(
        event_type="signal.recorded",
        producer="test",
        family=TableFamily.SIGNAL,
        payload={"symbol": "EURUSD"},
        event_id=eid,
        idempotency_key="k1",
    )
    b = api.ingest_event(
        event_type="signal.recorded",
        producer="test",
        family=TableFamily.SIGNAL,
        payload={"symbol": "EURUSD"},
        event_id=eid,
        idempotency_key="k1",
    )
    assert a.disposition is ApiDisposition.COMMITTED
    assert b.disposition is ApiDisposition.DUPLICATE_IGNORED
    assert api.store.last_sequence() == 1
    events = api.store.list_events()
    assert events[0]["event_id"] == eid


def test_outbox_transactional_with_event(tmp_path: Path):
    api = _api(tmp_path)
    result = api.ingest_event(
        event_type="order.recorded",
        producer="test",
        family=TableFamily.ORDER,
        payload={"client_order_id": "c-1"},
        idempotency_key="order-c-1",
    )
    assert result.disposition is ApiDisposition.COMMITTED
    pending = api.store.pending()
    assert len(pending) == 1
    assert pending[0]["event_id"] == str(result.record_id)
    published = api.dispatch_outbox()
    assert published[0]["state"] == "published"
    assert api.store.pending() == []


def test_inbox_effectively_once(tmp_path: Path):
    api = _api(tmp_path)
    seen: list[str] = []
    eid = str(uuid4())
    first = api.consume_inbox(eid, "pm5", lambda x: seen.append(x))
    second = api.consume_inbox(eid, "pm5", lambda x: seen.append(x))
    assert first.disposition is ApiDisposition.COMMITTED
    assert second.disposition is ApiDisposition.DUPLICATE_IGNORED
    assert seen == [eid]


def test_four_idempotency_edges(tmp_path: Path):
    api = _api(tmp_path)
    api.persist_order("co-1", {"state": "accepted"})
    dup_order = api.persist_order("co-1", {"state": "accepted"})
    assert dup_order.disposition is ApiDisposition.DUPLICATE_IGNORED

    api.persist_execution("co-1", "mt5_demo_sim", {"fill": 1}, venue_callback_id="cb-1")
    dup_cb = api.persist_execution("co-1", "mt5_demo_sim", {"fill": 1}, venue_callback_id="cb-1")
    assert dup_cb.disposition is ApiDisposition.DUPLICATE_IGNORED

    first = api.apply_projection_event("pos", 1, {"EURUSD": "1"})
    second = api.apply_projection_event("pos", 1, {"EURUSD": "9"})
    assert first.disposition is ApiDisposition.COMMITTED
    assert second.disposition is ApiDisposition.DUPLICATE_IGNORED
    stored = api.store.get_projection("pos")
    assert "1" in stored["payload_json"]


def test_projection_rebuild_deterministic(tmp_path: Path):
    api = _api(tmp_path)
    api.persist_signal("EURUSD", {"bias": "long"}, idempotency_key="s1")
    api.persist_signal("GBPUSD", {"bias": "short"}, idempotency_key="s2")
    a = api.rebuild_projections()
    b = api.rebuild_projections()
    assert a == b
    assert a["last_seq"] >= 2


def test_integrity_and_repair_does_not_rewrite(tmp_path: Path):
    api = _api(tmp_path)
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"n": 1})
    ok = api.check_integrity()
    assert ok.state == "valid"
    api.store._exec("UPDATE events SET prev_hash='tampered' WHERE sequence_no=1")
    bad = api.check_integrity()
    assert bad.state == "compromised"
    original = api.store.list_events()[0]["payload_json"]
    repaired = api.repair(bad)
    assert repaired.disposition is ApiDisposition.COMPROMISED
    assert api.store.list_events()[0]["payload_json"] == original
    assert api.store.last_sequence() >= 2


def test_recon_without_venue_never_silent_pass(tmp_path: Path):
    api = _api(tmp_path)
    refused = api.persist_reconciliation("local-1", None, "pass", {})
    assert refused.disposition is ApiDisposition.REJECTED
    ok = api.persist_reconciliation("local-1", None, "matched", {})
    assert ok.disposition is ApiDisposition.COMMITTED
    open_rows = api.store.list_open()
    assert open_rows[0]["state"] == "degraded"


def test_broker_truth_label_rejected(tmp_path: Path):
    api = _api(tmp_path)
    r = api.persist_execution("o1", "pm5_broker", {"fill": True})
    assert r.disposition is ApiDisposition.REJECTED


def test_flag_off_null_storage():
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="test", profile="test")
    container = build_container(settings)
    assert isinstance(container.registry.get("pm8_persistence").instance, NullStorage)


def test_flag_on_binds_module():
    settings = load_settings(
        config_path=TEST_YAML,
        environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_PERSISTENCE": "true"},
        cli_mode="test",
        profile="test",
    )
    container = build_container(settings)
    inst = container.registry.get("pm8_persistence").instance
    assert isinstance(inst, PM8PersistenceModule)
    assert inst.api.health()["api_version"] == "v1"


def test_query_requires_authorization(tmp_path: Path):
    api = _api(tmp_path)
    with pytest.raises(PermissionError):
        api.query_events(actor="x", authorized=False)
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={})
    rows = api.query_events(actor="auditor", authorized=True, limit=10)
    assert rows
