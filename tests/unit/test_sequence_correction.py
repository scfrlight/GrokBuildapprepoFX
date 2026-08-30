"""Correction wave: freeze machinery, reclassification, Sequence 13 reuse."""

from __future__ import annotations

from pathlib import Path

import pytest

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import FeatureFlagError
from botmoduleproject1.app.sequence_gate import (
    CANONICAL_OPERATOR_SEQUENCE,
    CANONICAL_SEQUENCES,
    assert_operator_not_frozen,
)
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.modules.pm8_operator.module import PM8OperatorModule
from botmoduleproject1.modules.pm8_persistence.module import PM8PersistenceModule
from tests.unit.pm5_support import Clock
from tests.unit.pm8_support import actor, pm8_module

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def test_canonical_map_has_09_to_13():
    assert CANONICAL_SEQUENCES[9] == "pm8_database_consolidation"
    assert CANONICAL_SEQUENCES[10] == "pm8a_migration_backup_recovery"
    assert CANONICAL_SEQUENCES[11] == "pm6_mt5_execution_exit_engine"
    assert CANONICAL_SEQUENCES[12] == "unified_runtime_orchestrator"
    assert CANONICAL_SEQUENCES[13] == "pm9_operator_ux_telegram_control"
    assert CANONICAL_OPERATOR_SEQUENCE == 13


def test_freeze_blocks_when_set(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("botmoduleproject1.app.sequence_gate.OPERATOR_PLANE_FROZEN", True)
    with pytest.raises(FeatureFlagError, match="FROZEN"):
        assert_operator_not_frozen("pm8_operator", "enable_pm8_operator")
    monkeypatch.setattr("botmoduleproject1.app.feature_flags.assert_operator_not_frozen", assert_operator_not_frozen)
    with pytest.raises(FeatureFlagError, match="FROZEN"):
        load_settings(
            config_path=TEST_YAML,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_OPERATOR": "true"},
            cli_mode="test",
            profile="test",
        )


def test_sequence13_reuses_operator_and_binds_persistence():
    settings = load_settings(
        config_path=TEST_YAML,
        environ={
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_OPERATOR": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_HITL": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_COMMAND_AUDIT": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_PERSISTENCE": "true",
        },
        cli_mode="test",
        profile="test",
    )
    container = build_container(settings, overrides={"clock": Clock()})
    op = container.registry.get("pm8_operator").instance
    storage = container.registry.get("pm8_persistence").instance
    assert isinstance(op, PM8OperatorModule)
    assert isinstance(storage, PM8PersistenceModule)
    receipt = op.handle_text("/status", actor())
    assert "persistence=v1" in receipt.message
    assert "live=false" in receipt.message


def test_existing_operator_module_still_constructs():
    mod = pm8_module()
    r = mod.handle_text("/doctor", actor())
    assert "execution_permitted=false" in r.message
