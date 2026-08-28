"""Feature flag safety classification and env-only dangerous opt-in."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.exceptions import FeatureFlagError, LiveTradingDisabledError, SettingsError
from botmoduleproject1.app.feature_flags import FEATURE_FLAG_CATALOG, SafetyClassification
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.contracts.v1.journal import EventType

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "configs" / "base.example.yaml"
DEMO = ROOT / "configs" / "demo.example.yaml"


def test_catalog_has_required_stubs() -> None:
    names = {spec.name for spec in FEATURE_FLAG_CATALOG}
    assert "enable_pm4_risk_gate" in names
    assert "enable_pm5_execution" in names
    assert "enable_pm5_simulation" in names
    assert "enable_pm5_broker_adapter" in names
    assert "enable_live_execution" in names
    assert "enable_pm6_post_trade" in names
    assert "enable_pm6_surveillance" in names
    assert "enable_pm7_persistence" in names
    assert "enable_pm7_journal" in names
    assert "enable_telegram_control" in names
    dangerous = [s for s in FEATURE_FLAG_CATALOG if s.safety is SafetyClassification.DANGEROUS]
    assert dangerous
    assert all(s.default is False for s in FEATURE_FLAG_CATALOG)


def test_flags_default_false() -> None:
    settings = load_settings(config_path=BASE, environ={}, cli_mode="doctor")
    enabled = settings.feature_flags.enabled_map()
    assert enabled
    assert all(value is False for value in enabled.values())


def test_dangerous_flag_yaml_true_fails() -> None:
    with pytest.raises((FeatureFlagError, SettingsError), match="dangerous"):
        load_settings(
            config_path=BASE,
            environ={},
            cli_mode="doctor",
            extra={"feature_flags": {"execution": True}},
        )


def test_dangerous_flag_env_opt_in_demo() -> None:
    settings = load_settings(
        config_path=DEMO,
        environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_EXECUTION": "true"},
        cli_mode="doctor",
    )
    assert settings.feature_flags.execution is True
    assert "execution" in settings.feature_flags.env_opt_in
    catalog = {flag.name: flag for flag in settings.feature_catalog()}
    assert catalog["enable_pm5_execution"].enabled is True
    assert catalog["enable_pm5_execution"].source == "env"


def test_live_trading_flag_always_refused() -> None:
    with pytest.raises(LiveTradingDisabledError):
        load_settings(
            config_path=BASE,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_LIVE_TRADING": "true"},
            cli_mode="doctor",
        )


def test_dangerous_flag_writes_journal_audit() -> None:
    settings, container, runtime = bootstrap(
        config_path=DEMO,
        cli_mode="doctor",
        environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_EXECUTION": "true"},
    )
    storage = container.registry.get("pm8_persistence").instance
    entries = getattr(storage, "entries", [])
    assert entries
    assert any(
        e.event_type is EventType.CONFIG and "enable_pm5_execution" in e.summary
        for e in entries
    )
    runtime.stop()
    blob = str(settings.public_dict())
    assert "true" in blob or settings.feature_flags.execution is True
