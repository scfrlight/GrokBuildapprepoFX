"""Safety: flags off, no live, no MT5, no PM2/PM3 bypass, submit raises."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import ExecutionDisabledError, FeatureFlagError, LiveTradingDisabledError, SettingsError
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution
from botmoduleproject1.contracts.v1.execution import ExecutionRejectReason, OrderRequest
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.pm5_execution.module import PM5ExecutionModule
from tests.unit.pm4_support import AS_OF, admitted_bundle
from tests.unit.pm5_support import pm5_module

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"
BASE = ROOT / "configs" / "base.example.yaml"
DEMO = ROOT / "configs" / "demo.example.yaml"


def test_default_bind_is_disabled_execution() -> None:
    settings = load_settings(config_path=TEST_YAML, environ={})
    container = build_container(settings)
    exe = container.registry.get("pm5_execution").instance
    assert isinstance(exe, DisabledExecution)
    with pytest.raises(ExecutionDisabledError):
        exe.submit(
            OrderRequest(
                causation_id=__import__("uuid").uuid4(),
                idempotency_key="nope",
                occurred_at=utc_now(),
                intent_id=__import__("uuid").uuid4(),
                risk_verdict_id=__import__("uuid").uuid4(),
                symbol="EURUSD",
                direction=Direction.BUY,
                entry_type=EntryType.MARKET,
                volume=__import__("decimal").Decimal("1"),
            )
        )


def test_yaml_flags_false() -> None:
    settings = load_settings(config_path=BASE, environ={})
    assert settings.feature_flags.execution is False
    assert settings.feature_flags.pm5_simulation is False
    assert settings.feature_flags.pm5_broker_adapter is False
    assert settings.feature_flags.mt5_demo_execution is False
    assert settings.feature_flags.live_execution is False
    assert settings.pm5_execution.auto_rearm is False
    assert settings.pm5_execution.broker_adapter_enabled is False
    assert settings.pm5_execution.mt5_enabled is False


def test_simulation_flag_on_in_test_binds_module() -> None:
    settings = load_settings(
        config_path=TEST_YAML,
        environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_SIMULATION": "true"},
        cli_mode="test",
        profile="test",
    )
    assert settings.feature_flags.pm5_simulation is True
    container = build_container(settings)
    exe = container.registry.get("pm5_execution").instance
    assert isinstance(exe, PM5ExecutionModule)
    assert exe.mode.value == "simulation"


def test_simulation_flag_rejected_in_demo() -> None:
    with pytest.raises((FeatureFlagError, SettingsError)):
        load_settings(
            config_path=DEMO,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_SIMULATION": "true"},
            profile="demo",
        )


def test_broker_and_mt5_flags_refused() -> None:
    with pytest.raises((FeatureFlagError, SettingsError), match="refused|dangerous"):
        load_settings(
            config_path=TEST_YAML,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_BROKER_ADAPTER": "true"},
            profile="test",
        )
    with pytest.raises((FeatureFlagError, SettingsError, LiveTradingDisabledError)):
        load_settings(
            config_path=TEST_YAML,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_MT5_DEMO_EXECUTION": "true"},
            profile="test",
        )


def test_live_execution_flag_refused() -> None:
    with pytest.raises(LiveTradingDisabledError):
        load_settings(
            config_path=BASE,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_LIVE_EXECUTION": "true"},
        )


def test_live_profile_refused() -> None:
    with pytest.raises(LiveTradingDisabledError):
        load_settings(config_path=BASE, environ={}, profile="live")


def test_module_submit_always_raises() -> None:
    mod = pm5_module()
    with pytest.raises(ExecutionDisabledError, match="disabled"):
        mod.submit(
            OrderRequest(
                causation_id=__import__("uuid").uuid4(),
                idempotency_key="still-no",
                occurred_at=AS_OF,
                intent_id=__import__("uuid").uuid4(),
                risk_verdict_id=__import__("uuid").uuid4(),
                symbol="EURUSD",
                direction=Direction.BUY,
                entry_type=EntryType.MARKET,
                volume=__import__("decimal").Decimal("1"),
            )
        )


def test_no_pm2_pm3_bypass() -> None:
    # ingest has no RankedCandidate / TradeIntent / ForecastOutput parameter
    import inspect

    sig = inspect.signature(PM5ExecutionModule.ingest)
    assert "candidate" not in sig.parameters
    assert "intent" not in sig.parameters
    assert "forecast" not in sig.parameters


def test_feature_disabled_when_simulation_off() -> None:
    pub = pm5_module(simulation_enabled=False).ingest(admitted_bundle(key="off"), direction=Direction.BUY)
    assert ExecutionRejectReason.FEATURE_DISABLED in pub.receipt.reasons
    assert pub.receipt.accepted is False
    assert pub.broker_side_effect is False


def test_publication_forbids_mt5_and_live() -> None:
    from pydantic import ValidationError

    from botmoduleproject1.contracts.v1.execution import (
        ExecutionIntentReceipt,
        ExecutionMode,
        ExecutionPublicationBundle,
    )

    receipt = ExecutionIntentReceipt(accepted=False)
    with pytest.raises(ValidationError):
        ExecutionPublicationBundle(
            occurred_at=AS_OF,
            receipt=receipt,
            mt5_used=True,
        )
    with pytest.raises(ValidationError):
        ExecutionPublicationBundle(
            occurred_at=AS_OF,
            receipt=receipt,
            broker_side_effect=True,
        )
    with pytest.raises(ValidationError):
        ExecutionPublicationBundle(
            occurred_at=AS_OF,
            receipt=receipt,
            execution_mode=ExecutionMode.LIVE,
        )
