from botmoduleproject1.contracts.v1.persistence import QuerySpec
from tests.unit.pm7_support import make_event, pm7_module


def test_authorized_query_with_limit():
    mod = pm7_module()
    mod.ingest(make_event(idempotency_key="q1"))
    spec = QuerySpec(actor="ops", authorized=True, symbol="EURUSD", limit=10)
    result = mod.query(spec)
    assert result.authorized is True
    assert result.access == "granted"
    assert result.event_ids
    assert result.provenance
    assert result.limit <= 50


def test_unauthorized_query_rejected():
    mod = pm7_module()
    mod.ingest(make_event())
    spec = QuerySpec(actor="ops", authorized=False)
    result = mod.query(spec)
    assert result.authorized is False
    assert result.access == "rejected"
    assert "unauthorized" in result.reasons


def test_export_manifest_checksum_no_secrets():
    mod = pm7_module()
    mod.ingest(make_event(event_payload={"ok": True, "password": "nope"}))
    pkg = mod.export_package()
    assert pkg.checksum
    dumped = str(pkg.json_payload) + str(pkg.manifest)
    assert "nope" not in dumped
    assert "password" not in dumped.lower() or "password" not in str(pkg.json_payload.get("event_payload", {}))
