"""PM2 feature-flag, fail-closed, UTC, no execution leakage."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.adapters.clock.system import FakeClock
from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.capabilities import Capability
from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import ExecutionDisabledError, FeatureFlagError
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import NullMarketData
from botmoduleproject1.contracts.v1 import Direction, EntryType, OrderRequest, Timeframe
from botmoduleproject1.contracts.v1.time import UTC, utc_now
from botmoduleproject1.modules.pm2_market_context.module import PM2Module

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "configs" / "base.example.yaml"
TEST = ROOT / "configs" / "test.example.yaml"
DEMO = ROOT / "configs" / "demo.example.yaml"
RESEARCH = ROOT / "configs" / "research.example.yaml"
AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)
FLAG = "BOTMODULEPROJECT1_FEATURE__ENABLE_PM2_MARKET_DATA"


def test_yaml_flag_stays_false() -> None:
    for path in (BASE, TEST, DEMO, RESEARCH):
        settings = load_settings(config_path=path, environ={}, cli_mode="doctor")
        assert settings.feature_flags.market_data is False
        assert settings.feature_flags.enabled_map()["enable_pm2_market_data"] is False


def test_default_container_uses_null_market_data() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    container = build_container(settings)
    inst = container.registry.get("pm2_market_context").instance
    assert isinstance(inst, NullMarketData)
    bundle = inst.scan(AS_OF)
    assert bundle.shortlist == ()
    assert bundle.diagnostics_summary.get("enabled") is False


def test_env_opt_in_test_profile_wires_pm2() -> None:
    settings = load_settings(
        config_path=TEST,
        environ={FLAG: "true"},
        cli_mode="test",
    )
    assert settings.feature_flags.market_data is True
    container = build_container(settings, overrides={"clock": FakeClock(AS_OF)})
    inst = container.registry.get("pm2_market_context").instance
    assert isinstance(inst, PM2Module)
    meta = inst.metadata()
    assert Capability.MARKET_DATA in meta.capabilities
    assert Capability.REGIME_DETECTION in meta.capabilities
    bundle = inst.scan(AS_OF)
    assert bundle.producer == "pm2_market_context"
    assert bundle.as_of.tzinfo is not None
    assert bundle.as_of.utcoffset().total_seconds() == 0


def test_env_opt_in_research_profile_allowed() -> None:
    settings = load_settings(
        config_path=RESEARCH,
        environ={FLAG: "true"},
        cli_mode="research",
        profile="research",
    )
    assert settings.feature_flags.market_data is True


def test_flag_rejected_in_demo() -> None:
    with pytest.raises(FeatureFlagError, match="enable_pm2_market_data"):
        load_settings(
            config_path=DEMO,
            environ={FLAG: "true"},
            cli_mode="doctor",
        )


def test_no_execution_leakage_when_pm2_scans() -> None:
    settings, container, runtime = bootstrap(
        config_path=TEST,
        cli_mode="test",
        environ={FLAG: "true"},
        overrides={"clock": FakeClock(AS_OF)},
    )
    pm2 = container.registry.get("pm2_market_context").instance
    execution = container.registry.get("pm5_execution").instance
    risk = container.registry.get("pm4_risk").instance
    bundle = pm2.scan(AS_OF)
    blob = str(bundle.model_dump(mode="json"))
    assert "TradeIntent" not in blob
    assert "OrderRequest" not in blob
    assert bundle.diagnostics_summary.get("orders") is False
    assert risk.evaluate  # still the deny gate
    request = OrderRequest(
        causation_id=uuid4(),
        idempotency_key="pm2-leak-test",
        occurred_at=utc_now(),
        intent_id=uuid4(),
        risk_verdict_id=uuid4(),
        symbol="EURUSD",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
        volume="0.01",
    )
    with pytest.raises(ExecutionDisabledError):
        execution.submit(request)
    runtime.stop()
    assert settings.safety.live_trading_enabled is False


def test_utc_identity_on_ranked_candidates() -> None:
    settings = load_settings(
        config_path=TEST, environ={FLAG: "true"}, cli_mode="test"
    )
    container = build_container(settings, overrides={"clock": FakeClock(AS_OF)})
    bundle = container.registry.get("pm2_market_context").instance.scan(AS_OF)
    for item in (*bundle.shortlist, *bundle.watchlist):
        assert item.event_id
        assert item.correlation_id
        assert item.as_of.tzinfo is not None
        assert item.context.as_of.tzinfo is not None
        assert item.producer == "pm2_market_context"


def test_fail_closed_stale_bars_empty_shortlist() -> None:
    from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
    from botmoduleproject1.modules.pm2_market_context.config.defaults import DEFAULT_PM2_CONFIG
    from botmoduleproject1.modules.pm2_market_context.scanner.freshness import classify

    old = datetime(2020, 1, 2, 12, 0, tzinfo=UTC)
    frozen = PM2Module(DEFAULT_PM2_CONFIG, FakeClock(old))
    far = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
    bars = frozen.feed.bars("EURUSD", Timeframe.H1)
    status = classify(bars, Timeframe.H1, far, stale_after_bars=3)
    assert status is DataQualityStatus.STALE


def test_pm2_does_not_implement_latest_signal() -> None:
    settings = load_settings(
        config_path=TEST, environ={FLAG: "true"}, cli_mode="test"
    )
    container = build_container(settings, overrides={"clock": FakeClock(AS_OF)})
    pm2 = container.registry.get("pm2_market_context").instance
    assert getattr(pm2, "latest_signal", None) is None
    bar = pm2.latest_bar("EURUSD", Timeframe.H1)
    assert bar is not None
