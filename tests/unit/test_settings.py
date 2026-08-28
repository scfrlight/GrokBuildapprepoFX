"""Settings validation, fingerprint, fail-fast live disable."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.exceptions import LiveTradingDisabledError, SettingsError
from botmoduleproject1.app.settings import load_settings

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "configs" / "base.example.yaml"
TEST = ROOT / "configs" / "test.example.yaml"


def test_loads_example_yaml() -> None:
    settings = load_settings(config_path=BASE, environ={}, cli_mode="doctor")
    assert settings.safety.trading_mode == "demo"
    assert settings.safety.live_trading_enabled is False
    assert settings.app.timezone == "UTC"
    assert settings.mt5.enabled is False


def test_fingerprint_is_stable_and_hex() -> None:
    a = load_settings(config_path=TEST, environ={}, cli_mode="test")
    b = load_settings(config_path=TEST, environ={}, cli_mode="test")
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64
    int(a.fingerprint(), 16)


def test_fingerprint_redacts_secrets() -> None:
    settings = load_settings(
        config_path=BASE,
        environ={"MT5_PASSWORD": "super-secret-value"},
        cli_mode="doctor",
    )
    dumped = settings.public_dict()
    blob = str(dumped)
    assert "super-secret-value" not in blob
    assert dumped["mt5"]["password"] in {"present", "absent"}


def test_live_flag_fail_fast() -> None:
    with pytest.raises(LiveTradingDisabledError, match="LIVE TRADING IS DISABLED"):
        load_settings(
            config_path=BASE,
            environ={"LIVE_TRADING_ENABLED": "true"},
            cli_mode="doctor",
        )


def test_live_cli_mode_fail_fast() -> None:
    with pytest.raises(LiveTradingDisabledError, match="mode=live"):
        load_settings(config_path=BASE, environ={}, cli_mode="live")


def test_live_trading_mode_fail_fast() -> None:
    with pytest.raises(LiveTradingDisabledError):
        load_settings(
            config_path=BASE,
            environ={"TRADING_MODE": "live"},
            cli_mode="doctor",
        )


def test_enabled_adapter_requires_secret() -> None:
    with pytest.raises(SettingsError, match="Telegram"):
        load_settings(
            config_path=BASE,
            environ={},
            cli_mode="doctor",
            extra={"telegram": {"enabled": True}},
        )


def test_env_overrides_symbol() -> None:
    settings = load_settings(
        config_path=BASE,
        environ={"DEFAULT_SYMBOL": "GBPUSD"},
        cli_mode="test",
    )
    assert settings.app.default_symbol == "GBPUSD"
