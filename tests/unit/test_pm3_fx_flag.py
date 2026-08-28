"""Feature flag wiring for PM3 forecasting / QRF."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.adapters.clock.system import FakeClock
from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.settings import load_settings
from tests.unit.pm3fx_support import AS_OF, confirmed_bars, forecasting_module, make_intent

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "configs" / "test.example.yaml"
FLAG = "BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING"


def test_flag_off_null_model_returns_none() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    assert settings.feature_flags.forecasting is False
    container = build_container(settings)
    inst = container.registry.get("pm3_forecasting").instance
    assert inst.__class__.__name__ == "NullModel"
    assert inst.forecast(make_intent()) is None


def test_yaml_keeps_forecasting_false() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    assert settings.feature_flags.forecasting is False
    assert settings.pm3_forecasting.horizon_bars == 4
    assert settings.pm3_forecasting.observe_only is True


def test_flag_on_via_env_wires_module() -> None:
    settings = load_settings(
        config_path=TEST,
        environ={FLAG: "true"},
        cli_mode="test",
    )
    assert settings.feature_flags.forecasting is True
    container = build_container(settings, overrides={"clock": FakeClock(AS_OF)})
    inst = container.registry.get("pm3_forecasting").instance
    assert inst.__class__.__name__ == "PM3ForecastingModule"
    out = inst.forecast(make_intent())
    assert out is not None
    assert out.producer == "pm3_forecasting"


def test_flag_on_via_override() -> None:
    settings = load_settings(config_path=TEST, environ={}, cli_mode="test")
    mod = forecasting_module()
    container = build_container(
        settings, overrides={"clock": FakeClock(AS_OF), "forecasting": mod}
    )
    inst = container.registry.get("pm3_forecasting").instance
    assert inst is mod
    out = inst.forecast_with_bars(make_intent(key="ov"), confirmed_bars())
    assert out is not None


def test_module_flag_off_returns_none() -> None:
    mod = forecasting_module(enabled=False)
    assert mod.forecast_with_bars(make_intent(key="off"), confirmed_bars()) is None
