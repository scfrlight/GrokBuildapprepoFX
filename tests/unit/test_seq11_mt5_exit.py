"""Canonical Sequence 11 — Demo MT5 routing, idempotency, exits. Live remains closed."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from botmoduleproject1.adapters.mt5.capabilities import probe_environment
from botmoduleproject1.adapters.mt5.demo_gateway import DemoMt5Gateway
from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.exceptions import ExecutionDisabledError, LiveTradingDisabledError
from botmoduleproject1.contracts.v1.risk import RiskVerdict, RiskVerdictStatus
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.mt5_execution_engine import DemoRouter, ExitEngine, ExitState
from botmoduleproject1.modules.pm5_execution.ems.mt5_adapter import Mt5BrokerAdapter

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def _allow(intent_id=None) -> RiskVerdict:
    from uuid import uuid4

    return RiskVerdict(
        intent_id=intent_id or uuid4(),
        occurred_at=utc_now(),
        status=RiskVerdictStatus.ALLOW,
    )


def test_live_account_probe_refused():
    with pytest.raises(ValueError):
        probe_environment(account_kind="live")


def test_sequence07_placeholder_still_blocked():
    adapter = Mt5BrokerAdapter()
    assert adapter.available() is False
    with pytest.raises(ExecutionDisabledError):
        adapter.submit(None, now=utc_now())  # type: ignore[arg-type]


def test_duplicate_and_retry_and_disconnect():
    gw = DemoMt5Gateway(simulated=True, max_retries=2)
    gw.connect()
    v = _allow()
    router = DemoRouter(gw)
    a = router.route(v, client_order_id="c1", quantity="0.1")
    b = router.route(v, client_order_id="c1", quantity="0.1")
    assert a["accepted"] is True
    assert a["venue_ticket"].startswith("DEMO-")
    assert b["duplicate"] is True
    gw.disconnect()
    recon = gw.reconcile("c1")
    assert recon["state"] == "degraded"
    assert recon["silent_pass"] is False
    gw.reconnect()
    recon2 = gw.reconcile("c1")
    assert recon2["state"] == "matched_demo"


def test_non_allow_cannot_reach_gateway():
    gw = DemoMt5Gateway(simulated=True)
    gw.connect()
    from uuid import uuid4

    deny = RiskVerdict(intent_id=uuid4(), occurred_at=utc_now(), status=RiskVerdictStatus.DENY)
    with pytest.raises(ExecutionDisabledError):
        DemoRouter(gw).route(deny, client_order_id="x", quantity="0.1")


def test_exit_engine_sl_tp_be_time():
    engine = ExitEngine()
    plan = engine.arm(
        symbol="EURUSD",
        side="buy",
        entry=Decimal("1.1000"),
        sl=Decimal("1.0900"),
        tp=Decimal("1.1200"),
    )
    engine.on_price(plan, Decimal("1.1100"))
    assert plan.state is ExitState.BREAKEVEN
    assert plan.sl == Decimal("1.1000")
    engine.on_price(plan, Decimal("1.1200"))
    assert plan.state is ExitState.CLOSED
    assert "tp" in plan.events


def test_live_cli_still_fail_closed():
    with pytest.raises(LiveTradingDisabledError):
        bootstrap(config_path=TEST_YAML, cli_mode="live", profile="test")


def test_seq11_package_is_not_bare_pm6():
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("botmoduleproject1.modules.pm6_execution")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("botmoduleproject1.modules.pm5_execution.demo_routing")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("botmoduleproject1.modules.pm5_execution.exit_engine")
    from botmoduleproject1.modules import mt5_execution_engine

    assert mt5_execution_engine.DemoRouter is DemoRouter
