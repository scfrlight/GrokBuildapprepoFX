"""Multi-profile load, capabilities, and live hard-block."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.capabilities import Capability
from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import LiveTradingDisabledError
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.profiles import PROFILE_POLICIES, ProfileName, policy_for
from botmoduleproject1.app.runtime import Runtime
from botmoduleproject1.app.settings import load_settings

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("demo.example.yaml", ProfileName.DEMO),
        ("test.example.yaml", ProfileName.TEST),
        ("backtest.example.yaml", ProfileName.BACKTEST),
        ("research.example.yaml", ProfileName.RESEARCH),
    ],
)
def test_profile_yaml_loads(filename: str, expected: ProfileName) -> None:
    settings = load_settings(
        config_path=ROOT / "configs" / filename,
        environ={},
        cli_mode="doctor",
    )
    assert settings.profile is expected
    policy = policy_for(expected)
    assert settings.profile_policy.name is expected
    assert Capability.PLATFORM in policy.allowed_capabilities
    assert "order_send" in policy.forbidden_operations
    assert policy.allows_execution is False
    assert policy.may_enter_running is True


def test_live_profile_yaml_cannot_load() -> None:
    with pytest.raises(LiveTradingDisabledError, match="LIVE TRADING IS DISABLED"):
        load_settings(
            config_path=ROOT / "configs" / "live.example.yaml",
            environ={},
            cli_mode="doctor",
        )


def test_live_profile_cli_override_cannot_load() -> None:
    with pytest.raises(LiveTradingDisabledError, match="profile=live"):
        load_settings(
            config_path=ROOT / "configs" / "test.example.yaml",
            environ={},
            cli_mode="doctor",
            profile="live",
        )


def test_live_profile_cannot_reach_running() -> None:
    settings = load_settings(
        config_path=ROOT / "configs" / "test.example.yaml",
        environ={},
        cli_mode="test",
    )
    settings.profile = ProfileName.LIVE
    container = build_container(settings)
    with pytest.raises(LiveTradingDisabledError):
        Runtime(container).start()
    assert container.lifecycle.state is not LifecycleState.RUNNING
    assert container.lifecycle.state is LifecycleState.FAILED


def test_all_catalogued_profiles_exist() -> None:
    assert set(PROFILE_POLICIES) == set(ProfileName)
    assert PROFILE_POLICIES[ProfileName.LIVE].may_enter_running is False
    assert PROFILE_POLICIES[ProfileName.DEMO].allows_mt5_demo_network is True
    assert PROFILE_POLICIES[ProfileName.TEST].allows_mt5_demo_network is False
