"""Sequence 15 Phase 1: demo-only readiness allowlist. LIVE stay fail-closed."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.exceptions import FeatureFlagError, LiveTradingDisabledError, SettingsError
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.sequence_gate import CANONICAL_SEQUENCES
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.contracts.v1.observability import ProbeState
from botmoduleproject1.modules.observability.demo_readiness import (
    evaluate_demo_readiness_allowlist,
)
from botmoduleproject1.modules.observability.health_model import TRANSITION_TABLE, evaluate

ROOT = Path(__file__).resolve().parents[2]
DEMO_YAML = ROOT / "configs" / "demo.example.yaml"
TEST_YAML = ROOT / "configs" / "test.example.yaml"
BASE_YAML = ROOT / "configs" / "base.example.yaml"

DEMO_FLAG_ENV = {"BOTMODULEPROJECT1_FEATURE__ENABLE_DEMO_TRADING_READINESS": "true"}


def test_canonical_sequence_15():
    assert CANONICAL_SEQUENCES[15] == "demo_only_trading_readiness_allowlist"


def test_default_path_trading_readiness_closed():
    settings = load_settings(config_path=DEMO_YAML, environ={}, cli_mode="observe", profile="demo")
    health, ready = evaluate(settings, lifecycle=LifecycleState.RUNNING, integrity_ok=True)
    assert health.trading_readiness is False
    assert ready.accept_trade is False
    assert ready.trading_readiness is ProbeState.FAIL


def test_demo_allowlist_opens_readiness_when_explicit():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="observe",
        profile="demo",
    )
    assert settings.feature_flags.demo_trading_readiness is True
    assert "demo_trading_readiness" in settings.feature_flags.env_opt_in
    health, ready = evaluate(
        settings,
        lifecycle=LifecycleState.RUNNING,
        integrity_ok=True,
        stale_data=False,
    )
    assert health.trading_readiness is True
    assert ready.accept_trade is True
    assert ready.trading_readiness is ProbeState.PASS
    decision = evaluate_demo_readiness_allowlist(
        settings, recovery_complete=True, stale_data=False, integrity_ok=True
    )
    assert decision.allowed is True
    assert decision.path == "demo_allowlist"
    assert "demo_allowlist_explicit" in decision.reasons
    assert "pm4_remains_exclusive_risk_gate" in decision.reasons


def test_demo_allowlist_yaml_cannot_enable():
    with pytest.raises((FeatureFlagError, SettingsError), match="dangerous"):
        load_settings(
            config_path=DEMO_YAML,
            environ={},
            cli_mode="observe",
            profile="demo",
            extra={"feature_flags": {"demo_trading_readiness": True}},
        )


def test_demo_flag_refused_outside_demo_profile():
    with pytest.raises((FeatureFlagError, SettingsError), match="not allowed in profile"):
        load_settings(
            config_path=TEST_YAML,
            environ=DEMO_FLAG_ENV,
            cli_mode="observe",
            profile="test",
        )


def test_paper_mode_cannot_open_allowlist():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="paper",
        profile="demo",
    )
    decision = evaluate_demo_readiness_allowlist(
        settings, recovery_complete=True, stale_data=False, integrity_ok=True
    )
    assert decision.allowed is False
    assert "paper_or_live_mode_refused" in decision.reasons
    health, ready = evaluate(settings, lifecycle=LifecycleState.RUNNING, integrity_ok=True)
    assert health.trading_readiness is False
    assert ready.accept_trade is False


def test_production_environment_refused():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="observe",
        profile="demo",
        extra={"app": {"environment": "production"}},
    )
    decision = evaluate_demo_readiness_allowlist(
        settings, recovery_complete=True, stale_data=False, integrity_ok=True
    )
    assert decision.allowed is False
    assert "production_environment_refused" in decision.reasons


def test_recovery_incomplete_keeps_closed():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="observe",
        profile="demo",
    )
    health, ready = evaluate(settings, lifecycle=LifecycleState.WIRED, integrity_ok=True)
    assert health.trading_readiness is False
    assert ready.accept_trade is False


def test_stale_data_keeps_closed():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="observe",
        profile="demo",
    )
    health, ready = evaluate(
        settings, lifecycle=LifecycleState.RUNNING, integrity_ok=True, stale_data=True
    )
    assert health.trading_readiness is False
    assert ready.accept_trade is False


def test_live_still_fail_closed():
    with pytest.raises(LiveTradingDisabledError):
        bootstrap(config_path=DEMO_YAML, cli_mode="live", environ=DEMO_FLAG_ENV, profile="demo")
    with pytest.raises(LiveTradingDisabledError):
        load_settings(
            config_path=BASE_YAML,
            environ={
                **DEMO_FLAG_ENV,
                "BOTMODULEPROJECT1_FEATURE__ENABLE_LIVE_TRADING": "true",
            },
            cli_mode="doctor",
        )


def test_broker_venue_still_unavailable_without_adapter():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="observe",
        profile="demo",
    )
    _health, ready = evaluate(settings, lifecycle=LifecycleState.RUNNING, integrity_ok=True)
    assert ready.broker_venue is ProbeState.UNAVAILABLE
    # Readiness may open; real MT5 remains not wired.
    assert ready.accept_trade is True


def test_transition_table_includes_demo_pass_row():
    rows = { (d, c): (s, h) for d, c, s, h in TRANSITION_TABLE }
    assert rows[("trading_readiness", "demo_allowlist_explicit")] == (ProbeState.PASS, False)
    assert rows[("trading_readiness", "live_profile")] == (ProbeState.FAIL, True)
    assert rows[("trading_readiness", "paper_mode")] == (ProbeState.FAIL, True)


def test_health_model_source_avoids_literal_true_kwargs():
    source = (
        ROOT / "botmoduleproject1" / "modules" / "observability" / "health_model.py"
    ).read_text(encoding="utf-8")
    assert "trading_readiness=True" not in source
    assert "accept_trade=True" not in source


def test_pm4_still_exclusive_mentioned_in_decision():
    settings = load_settings(
        config_path=DEMO_YAML,
        environ=DEMO_FLAG_ENV,
        cli_mode="observe",
        profile="demo",
    )
    decision = evaluate_demo_readiness_allowlist(
        settings, recovery_complete=True, stale_data=False, integrity_ok=True
    )
    assert "pm4_remains_exclusive_risk_gate" in decision.reasons
    assert "real_mt5_not_wired" in decision.reasons
