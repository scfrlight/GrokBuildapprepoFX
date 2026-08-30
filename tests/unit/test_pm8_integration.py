from pathlib import Path

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import FeatureFlagError
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import NullOperator
from botmoduleproject1.contracts.v1.operator import CommandDisposition
from botmoduleproject1.modules.pm8_operator.module import PM8OperatorModule
from botmoduleproject1.modules.pm9_operator_ux import PM8OperatorModule as Reexport
from tests.unit.pm5_support import Clock
from tests.unit.pm8_support import actor, pm8_module

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"
BASE = ROOT / "configs" / "base.example.yaml"


def test_flag_on_binds_pm8():
    settings = load_settings(
        config_path=TEST_YAML,
        environ={
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_OPERATOR": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_HITL": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_COMMAND_AUDIT": "true",
        },
        cli_mode="test",
        profile="test",
    )
    container = build_container(settings, overrides={"clock": Clock()})
    op = container.registry.get("pm8_operator").instance
    assert isinstance(op, PM8OperatorModule)
    assert op.is_ready() is True
    receipt = op.handle_text("/doctor", actor())
    assert receipt.disposition is CommandDisposition.ACCEPTED
    assert "execution_permitted=false" in receipt.message


def test_flag_off_null_operator():
    settings = load_settings(config_path=TEST_YAML, environ={})
    container = build_container(settings)
    assert isinstance(container.registry.get("pm8_operator").instance, NullOperator)
    assert container.registry.get("pm8_persistence").instance is not None


def test_telegram_flag_refused():
    try:
        load_settings(
            config_path=BASE,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_TELEGRAM_CONTROL": "true"},
            cli_mode="doctor",
        )
        raise AssertionError("telegram flag must be refused")
    except FeatureFlagError as exc:
        assert "refused" in str(exc).lower()


def test_yaml_cannot_enable_operator_in_demo():
    settings = load_settings(config_path=BASE, environ={}, cli_mode="doctor")
    assert settings.feature_flags.pm8_operator is False


def test_health_and_manifest():
    mod = pm8_module()
    checks = mod.health_checks(CheckKind.STARTUP)
    names = {c.name: c for c in checks}
    assert names["operator.no_mt5"].passed
    assert names["operator.no_telegram_api"].passed
    manifest = mod.manifest()
    assert "orders" in manifest["does_not"]
    assert manifest["execution_permitted"] is False


def test_pm9_reexport():
    assert Reexport is PM8OperatorModule


def test_audit_strips_secret_shaped_text():
    mod = pm8_module()
    mod.handle_text("/status token=abc", actor(), idempotency_key="aud")
    assert mod.audit.records
    assert "[redacted]" in mod.audit.records[-1]["text"] or "token" not in mod.audit.records[-1]["text"].lower() or "[redacted]" in str(mod.audit.records)
