"""Preflight success, failure, and secret-missing paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.exceptions import PreflightError, SettingsError
from botmoduleproject1.app.preflight import run_preflight
from botmoduleproject1.app.settings import load_settings

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "configs" / "test.example.yaml"
DEMO = ROOT / "configs" / "demo.example.yaml"


def test_preflight_passes_for_test_profile() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    report = run_preflight(settings)
    assert report.passed is True
    names = {c.name for c in report.checks}
    assert "python.version" in names
    assert "config.file" in names
    assert "profile.live_blocked" in names
    assert "secrets.required" in names
    assert "dependencies.pinned" in names
    assert "filesystem.permissions" in names


def test_preflight_fails_python_and_raises() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    with pytest.raises(PreflightError, match="python.version"):
        run_preflight(settings, python_version=(3, 10, 21), fail_fast=True)


def test_preflight_missing_secret_when_mt5_enabled() -> None:
    settings = load_settings(config_path=DEMO, environ={}, cli_mode="doctor")
    settings.mt5.enabled = True
    report = run_preflight(settings, fail_fast=False)
    assert report.passed is False
    secret = next(c for c in report.checks if c.name == "secrets.required")
    assert secret.passed is False
    assert "MT5_PASSWORD" in secret.message


def test_settings_fail_fast_mt5_without_password() -> None:
    with pytest.raises(SettingsError, match="password"):
        load_settings(
            config_path=DEMO,
            environ={},
            cli_mode="doctor",
            extra={"mt5": {"enabled": True}},
        )


def test_bootstrap_snapshot_includes_preflight() -> None:
    settings, _container, runtime = bootstrap(
        config_path=TEST, cli_mode="doctor", environ={}
    )
    assert runtime.last_snapshot is not None
    assert runtime.last_snapshot.preflight["passed"] is True
    assert runtime.last_snapshot.profile == "test"
    assert "platform" in runtime.last_snapshot.allowed_capabilities
    runtime.stop()
    assert settings.profile.value == "test"
