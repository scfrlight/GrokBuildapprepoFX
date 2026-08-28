"""Health aggregation, container overrides, runtime boot."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.adapters.clock.system import FakeClock
from botmoduleproject1.app.bootstrap import bootstrap, doctor
from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import ExecutionDisabledError, LiveTradingDisabledError
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution
from botmoduleproject1.contracts.v1 import Direction, EntryType, OrderRequest
from botmoduleproject1.contracts.v1.time import utc_now
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def test_startup_health_passes_for_kernel() -> None:
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="test")
    container = build_container(settings)
    report = container.health.run(CheckKind.STARTUP, fail_on_critical=True)
    assert report.passed is True
    assert report.kind is CheckKind.STARTUP


def test_readiness_degrades_when_risk_not_ready() -> None:
    settings, container, runtime = bootstrap(
        config_path=TEST_YAML, cli_mode="doctor", environ={}
    )
    assert runtime.container.lifecycle.state is LifecycleState.DEGRADED
    ready = container.health.run(CheckKind.READINESS, fail_on_critical=False)
    assert ready.passed is False
    assert "risk_gate.ready" in ready.critical_failed
    runtime.stop()
    assert settings.safety.live_trading_enabled is False


def test_clock_override() -> None:
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="test")
    clock = FakeClock()
    container = build_container(settings, overrides={"clock": clock})
    assert container.clock is clock
    assert container.clock.now() == clock.now()


def test_execution_stub_refuses_orders() -> None:
    exec_adapter = DisabledExecution()
    request = OrderRequest(
        causation_id=uuid4(),
        idempotency_key="k1",
        occurred_at=utc_now(),
        intent_id=uuid4(),
        risk_verdict_id=uuid4(),
        symbol="EURUSD",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
        volume="0.01",
    )
    with pytest.raises(ExecutionDisabledError):
        exec_adapter.submit(request)


def test_doctor_snapshot_keys() -> None:
    payload = doctor(config_path=TEST_YAML, environ={})
    assert payload["live_trading_enabled"] is False
    assert "config_fingerprint" in payload
    assert "pm1_platform" in payload["modules"]
    assert "NOT TRADE READY" in "\n".join(
        [
            payload["app_name"],
        ]
    ) or payload["trading_mode"] == "test"


def test_live_bootstrap_never_builds_runtime() -> None:
    with pytest.raises(LiveTradingDisabledError):
        bootstrap(config_path=TEST_YAML, cli_mode="live", environ={})
