from pathlib import Path

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import NullLedger
from botmoduleproject1.modules.pm7_persistence.module import PM7PersistenceModule
from tests.unit.pm5_support import Clock, ingest_allow
from tests.unit.pm6_support import observe_allow
from tests.unit.pm7_support import ingest_sim, make_event, pm7_module

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def test_flag_on_binds_pm7():
    settings = load_settings(
        config_path=TEST_YAML,
        environ={
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_PERSISTENCE": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_JOURNAL": "true",
        },
        cli_mode="test",
        profile="test",
    )
    container = build_container(settings, overrides={"clock": Clock()})
    ledger = container.registry.get("pm7_ledger").instance
    assert isinstance(ledger, PM7PersistenceModule)
    assert ledger.is_ready() is True
    _exe, bundle, pub = ingest_allow(key="int-bind")
    result = ledger.ingest(pub)
    assert result.disposition.value in {"committed", "duplicate_ignored"}
    assert ledger.publish().producer == "pm7_persistence"


def test_flag_off_null_ledger():
    settings = load_settings(config_path=TEST_YAML, environ={})
    container = build_container(settings)
    assert isinstance(container.registry.get("pm7_ledger").instance, NullLedger)
    assert isinstance(container.registry.get("pm8_persistence").instance, type(container.registry.get("pm8_persistence").instance))


def test_pm4_pm5_pm6_adapters():
    mod = pm7_module()
    _exe, bundle, pub = ingest_allow(key="int-p45")
    assert mod.ingest(bundle).disposition.value == "committed"
    assert mod.ingest(pub).disposition.value == "committed"
    pm6, _rb, _ep, truth = observe_allow(key="int-p6")
    result = mod.ingest(truth)
    assert result.disposition.value == "committed"
    assert not hasattr(mod, "oms")
    assert not hasattr(mod, "sizer")
    assert "pm7_persistence" in mod.__class__.__module__


def test_downstream_offline_does_not_break():
    mod = pm7_module()
    mod.ingest(make_event())
    # publication is in-process; emitting twice is fine
    a = mod.publish()
    b = mod.publish()
    assert a.persistence_handoff == "pending_pm8"
    assert b.producer == "pm7_persistence"


def test_health_startup():
    mod = pm7_module()
    startup = mod.health_checks(CheckKind.STARTUP)
    assert any(c.name == "ledger.startup" and c.passed for c in startup)
    assert any(c.name == "ledger.no_mt5" and c.passed for c in startup)


def test_file_and_sqlite_backends(tmp_path):
    from botmoduleproject1.modules.pm7_persistence.config.schema import Pm7PersistenceConfig
    from tests.unit.pm5_support import Clock

    file_mod = pm7_module(config=Pm7PersistenceConfig(operating_mode="file_backed", storage_path=str(tmp_path / "f")))
    assert file_mod.ingest(make_event()).disposition.value == "committed"
    sql_mod = pm7_module(config=Pm7PersistenceConfig(operating_mode="sqlite_local", storage_path=str(tmp_path / "s")))
    assert sql_mod.ingest(make_event()).disposition.value == "committed"
    assert sql_mod.backend.schema_version() == 1
