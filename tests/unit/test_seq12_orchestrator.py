"""Canonical Sequence 12 — unified runtime orchestrator."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
from botmoduleproject1.modules.pm8_persistence.migrations import MigrationService
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore
from botmoduleproject1.runtime.orchestrator import UnifiedRuntime

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def test_recovery_before_trading_and_stale_stop():
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="test", profile="test")
    container = build_container(settings)
    store = SqliteStore(":memory:")
    MigrationService(store).upgrade_to(2)
    api = PersistenceApiV1(store)
    orch = UnifiedRuntime(container, persistence_api=api)
    orch.state.running = True
    orch.state.recovery_complete = False
    out = orch.tick()
    assert out["ok"] is False
    assert out["reason"] == "recovery_before_trading"
    orch.start()
    assert orch.state.recovery_complete is True
    ok = orch.tick()
    assert ok["ok"] is True
    assert "market" in ok["trace"]
    assert "risk" in ok["trace"]
    assert "persistence" in ok["trace"]
    orch.mark_stale()
    stale = orch.tick()
    assert stale["reason"] == "stale_data_stop"
    orch.shutdown()
    assert orch.state.running is False


def test_compromised_ledger_halts():
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="test", profile="test")
    container = build_container(settings)
    store = SqliteStore(":memory:")
    api = PersistenceApiV1(store)
    from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily

    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"n": 1})
    store._exec("UPDATE events SET prev_hash='x' WHERE sequence_no=1")
    orch = UnifiedRuntime(container, persistence_api=api)
    orch.start()
    assert orch.state.halted is True
    assert orch.state.reason == "ledger_compromised"
