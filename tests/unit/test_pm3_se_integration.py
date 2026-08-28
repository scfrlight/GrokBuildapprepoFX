"""PM3-Strategy Engine kernel wiring."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.adapters.clock.system import FakeClock
from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.capabilities import Capability
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.contracts.v1.pm2 import PublicationBundle
from tests.unit.pm3se_support import AS_OF, engine, ranked_candidate

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "configs" / "test.example.yaml"
DEMO = ROOT / "configs" / "demo.example.yaml"
FLAG = "BOTMODULEPROJECT1_FEATURE__ENABLE_PM3_STRATEGY_ENGINE"


def test_flag_default_off_keeps_placeholder() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    assert settings.feature_flags.strategy_engine is False
    from botmoduleproject1.app.container import build_container

    container = build_container(settings)
    inst = container.registry.get("pm3_strategy_engine").instance
    assert inst.__class__.__name__ == "NullSignals"
    bundle = PublicationBundle(as_of=AS_OF)
    assert inst.evaluate_publication(bundle) == ()


def test_flag_on_in_test_wires_engine() -> None:
    settings = load_settings(
        config_path=TEST,
        environ={FLAG: "true"},
        cli_mode="test",
    )
    from botmoduleproject1.app.container import build_container

    clock = FakeClock(AS_OF)
    container = build_container(settings, overrides={"clock": clock})
    inst = container.registry.get("pm3_strategy_engine").instance
    assert inst.__class__.__name__ == "PM3StrategyEngineModule"
    caps = inst.metadata().capability_set
    assert Capability.TRADE_INTENT_GENERATION in caps
    assert Capability.STRATEGY_CONSENSUS in caps
    manifest = inst.manifest()
    assert manifest["display_name"] == "PM3-Strategy Engine"
    assert "orders" in manifest["does_not"]


def test_flag_rejected_in_demo() -> None:
    from botmoduleproject1.app.exceptions import FeatureFlagError
    import pytest

    with pytest.raises(FeatureFlagError):
        load_settings(config_path=DEMO, environ={FLAG: "true"}, cli_mode="doctor")


def test_no_pm5_or_telegram_imports() -> None:
    root = ROOT / "botmoduleproject1" / "modules" / "pm3_strategy_engine"
    blob = "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
    assert "from botmoduleproject1.adapters.mt5" not in blob
    assert "from botmoduleproject1.modules.pm5_execution" not in blob
    assert "aiogram" not in blob
    assert "from botmoduleproject1.adapters.telegram" not in blob
    assert "from botmoduleproject1.modules.pm3_forecasting" not in blob


def test_pm2_adapter_uses_public_contracts_only() -> None:
    from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.adapters import (
        pm2_context_adapter as adapter_mod,
    )
    src = Path(adapter_mod.__file__).read_text(encoding="utf-8")
    assert "modules.pm2_market_context.engines" not in src
    assert "modules.pm2_market_context.features" not in src
    assert "contracts.v1.pm2" in src


def test_bootstrap_with_flag_still_not_trade_ready() -> None:
    settings, container, runtime = bootstrap(
        config_path=TEST,
        cli_mode="doctor",
        environ={FLAG: "true"},
        overrides={"clock": FakeClock(AS_OF)},
    )
    assert settings.safety.live_trading_enabled is False
    se = container.registry.get("pm3_strategy_engine").instance
    risk = container.registry.get("pm4_risk").instance
    assert se.evaluate_candidate(ranked_candidate(handoff=True))
    from botmoduleproject1.contracts.v1 import ExposureSnapshot, utc_now
    from botmoduleproject1.contracts.v1.risk import RiskVerdictStatus
    from botmoduleproject1.contracts.v1.strategy import TradeIntent, Direction, EntryType

    intent = TradeIntent(
        idempotency_key="pipe-test",
        occurred_at=utc_now(),
        symbol="EURUSD",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
    )
    verdict = risk.evaluate(intent, ExposureSnapshot(as_of=utc_now()))
    assert verdict.status is RiskVerdictStatus.DENY
    runtime.stop()
