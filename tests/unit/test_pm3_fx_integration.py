"""PM3 forecasting / QRF kernel wiring."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.adapters.clock.system import FakeClock
from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.capabilities import Capability
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.settings import load_settings
from tests.unit.pm3fx_support import AS_OF, make_intent

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "configs" / "test.example.yaml"
FLAG = "BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING"


def test_container_wires_module_when_flag_on() -> None:
    settings = load_settings(
        config_path=TEST,
        environ={FLAG: "true"},
        cli_mode="test",
    )
    from botmoduleproject1.app.container import build_container

    clock = FakeClock(AS_OF)
    container = build_container(settings, overrides={"clock": clock})
    inst = container.registry.get("pm3_forecasting").instance
    assert inst.__class__.__name__ == "PM3ForecastingModule"
    caps = inst.metadata().capability_set
    assert Capability.FORECASTING in caps
    assert inst.metadata().critical is False
    out = inst.forecast(make_intent())
    assert out is not None
    assert out.model.model_id == "residual_quantile_envelope"


def test_health_is_non_critical() -> None:
    settings = load_settings(
        config_path=TEST,
        environ={FLAG: "true"},
        cli_mode="test",
    )
    from botmoduleproject1.app.container import build_container

    container = build_container(settings, overrides={"clock": FakeClock(AS_OF)})
    report = container.health.run(CheckKind.STARTUP, fail_on_critical=True)
    assert report.passed is True
    fx = [r for r in report.results if r.name.startswith("pm3_forecasting")]
    assert fx
    assert all(r.critical is False for r in fx)
    coverage = next(r for r in fx if r.name == "pm3_forecasting.coverage")
    assert coverage.passed is False  # insufficient data ≠ healthy
    assert coverage.critical is False


def test_bootstrap_with_flag_still_not_trade_ready() -> None:
    settings, container, runtime = bootstrap(
        config_path=TEST,
        cli_mode="doctor",
        environ={FLAG: "true"},
        overrides={"clock": FakeClock(AS_OF)},
    )
    assert settings.safety.live_trading_enabled is False
    fx = container.registry.get("pm3_forecasting").instance
    risk = container.registry.get("pm4_risk").instance
    out = fx.forecast(make_intent(key="boot"))
    assert out is not None
    from botmoduleproject1.contracts.v1 import ExposureSnapshot, utc_now
    from botmoduleproject1.contracts.v1.risk import RiskVerdictStatus

    verdict = risk.evaluate(make_intent(key="risk"), ExposureSnapshot(as_of=utc_now()))
    assert verdict.status is RiskVerdictStatus.DENY
    runtime.stop()
