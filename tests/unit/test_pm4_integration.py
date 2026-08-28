"""PM1 wiring, feature flag, PM2/PM3 contract integration, future PM5 handoff."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import FeatureFlagError, SettingsError
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution, NullRiskGate
from botmoduleproject1.contracts.v1.risk import HandoffEligibility, RiskVerdictStatus
from botmoduleproject1.modules.pm3_forecasting.module import PM3ForecastingModule
from botmoduleproject1.modules.pm3_forecasting.config.schema import Pm3ForecastingConfig
from botmoduleproject1.modules.pm4_risk_gate.module import PM4RiskGateModule
from tests.unit.pm3fx_support import confirmed_bars
from tests.unit.pm4_support import (
    AS_OF,
    admitted_bundle,
    make_candidate,
    make_exposure,
    make_intent,
    risk_module,
)

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"
DEMO_YAML = ROOT / "configs" / "demo.example.yaml"


class _Clock:
    def now(self):
        return AS_OF


def test_flag_on_in_test_binds_pm4_module() -> None:
    settings = load_settings(
        config_path=TEST_YAML,
        environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE": "true"},
        cli_mode="test",
        profile="test",
    )
    assert settings.feature_flags.risk_engine is True
    container = build_container(settings, overrides={"clock": _Clock()})
    risk = container.registry.get("pm4_risk").instance
    assert isinstance(risk, PM4RiskGateModule)
    assert risk.is_ready() is True
    ready = container.health.run(CheckKind.READINESS, fail_on_critical=False)
    assert "risk_gate.ready" not in ready.critical_failed


def test_flag_on_in_demo_rejected() -> None:
    with __import__("pytest").raises((FeatureFlagError, SettingsError)):
        load_settings(
            config_path=DEMO_YAML,
            environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE": "true"},
            cli_mode="doctor",
            profile="demo",
        )


def test_yaml_does_not_enable_pm4() -> None:
    settings = load_settings(config_path=ROOT / "configs" / "base.example.yaml", environ={})
    assert settings.feature_flags.risk_engine is False
    assert settings.pm4_risk_gate.auto_rearm is False


def test_integration_with_pm3_forecast_envelope() -> None:
    fx = PM3ForecastingModule(Pm3ForecastingConfig(), _Clock(), feature_enabled=True)
    candidate = make_candidate()
    intent = make_intent(key="fx-int", candidate_id=candidate.candidate_id, occurred_at=AS_OF)
    forecast = fx.forecast_with_bars(intent, confirmed_bars(count=80, as_of=AS_OF))
    assert forecast is not None
    gate = risk_module()
    bundle = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=intent.entry_price,
        session="london",
    )
    # envelope diagnostics are non-empty; may ALLOW or REDUCE/DENY on interval width
    assert bundle.forecast_id == forecast.forecast_id
    assert bundle.execution_permitted is False
    assert bundle.verdict.status in {RiskVerdictStatus.ALLOW, RiskVerdictStatus.DENY}


def test_allow_handoff_pending_pm5_and_execution_still_disabled() -> None:
    bundle = admitted_bundle(key="handoff")
    assert bundle.handoff_eligibility is HandoffEligibility.ELIGIBLE_PENDING_PM5
    assert isinstance(DisabledExecution(), DisabledExecution)
    settings = load_settings(config_path=TEST_YAML, environ={})
    container = build_container(settings)
    execution = container.registry.get("pm5_execution").instance
    assert isinstance(execution, DisabledExecution)


def test_pm4_health_startup_passes() -> None:
    gate = risk_module()
    startup = gate.health_checks(CheckKind.STARTUP)
    assert any(c.name == "risk_gate.startup" and c.passed for c in startup)
    live = gate.health_checks(CheckKind.LIVENESS)
    assert any(c.name == "risk_gate.liveness" and c.passed for c in live)


def test_metadata_and_manifest() -> None:
    gate = risk_module()
    meta = gate.metadata()
    assert meta.name == "pm4_risk"
    assert meta.critical is True
    man = gate.manifest()
    assert "orders" in man["does_not"]
    assert man["durable"] is False
