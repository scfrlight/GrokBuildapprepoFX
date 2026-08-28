from pathlib import Path

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import NullMonitoring
from botmoduleproject1.modules.pm6_post_trade.module import PM6PostTradeModule
from tests.unit.pm4_support import AS_OF
from tests.unit.pm5_support import Clock, ingest_allow
from tests.unit.pm6_support import observe_allow

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def test_flag_on_binds_pm6() -> None:
    settings = load_settings(
        config_path=TEST_YAML,
        environ={
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_POST_TRADE": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_SURVEILLANCE": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_INCIDENT_RESPONSE": "true",
        },
        cli_mode="test",
        profile="test",
    )
    container = build_container(settings, overrides={"clock": Clock()})
    mon = container.registry.get("pm6_monitoring").instance
    assert isinstance(mon, PM6PostTradeModule)
    assert mon.is_ready() is True
    _exe, bundle, pub = ingest_allow(key="int-bind")
    truth = mon.observe(pub, bundle)
    assert truth.producer == "pm6_post_trade"
    assert truth.durable is False


def test_flag_off_null_monitoring() -> None:
    settings = load_settings(config_path=TEST_YAML, environ={})
    container = build_container(settings)
    assert isinstance(container.registry.get("pm6_monitoring").instance, NullMonitoring)


def test_health_startup() -> None:
    from tests.unit.pm6_support import pm6_module

    mon = pm6_module()
    startup = mon.health_checks(CheckKind.STARTUP)
    assert any(c.name == "post_trade.startup" and c.passed for c in startup)
    assert any(c.name == "post_trade.no_mt5" and c.passed for c in startup)


def test_pm5_and_pm4_consumed_without_duplicating_oms() -> None:
    pm6, bundle, pub, truth = observe_allow(key="int-consume")
    assert pub.producer == "pm5_execution"
    assert bundle.producer == "pm4_risk_gate"
    assert truth.snapshot.execution_mode in {"simulation", "disabled"}
    assert not hasattr(pm6, "oms")
    assert not hasattr(pm6, "sizer")
    src = Path(pm6.__class__.__module__.replace(".", "/") + ".py")
    # module lives under pm6_post_trade
    assert "pm6_post_trade" in pm6.__class__.__module__
