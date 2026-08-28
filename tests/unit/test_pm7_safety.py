from pathlib import Path

import pytest

from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.contracts.v1.persistence import PersistenceMode, PersistencePublicationBundle
from botmoduleproject1.modules.pm7_persistence.config.schema import Pm7PersistenceConfig
from tests.unit.pm4_support import AS_OF
from tests.unit.pm7_support import make_event, pm7_module

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "configs" / "base.example.yaml"


def test_flags_default_false():
    settings = load_settings(config_path=BASE, environ={}, cli_mode="doctor")
    assert settings.feature_flags.pm7_persistence is False
    assert settings.feature_flags.pm7_journal is False


def test_cannot_enable_mt5_via_config():
    with pytest.raises(Exception):
        Pm7PersistenceConfig(mt5_enabled=True)


def test_production_durable_refused():
    with pytest.raises(Exception):
        Pm7PersistenceConfig(operating_mode="production_durable")
    with pytest.raises(Exception):
        PersistencePublicationBundle.model_validate(
            {
                "occurred_at": AS_OF,
                "mode": PersistenceMode.PRODUCTION_DURABLE,
            }
        )


def test_pm7_does_not_submit_orders():
    mod = pm7_module()
    assert not hasattr(mod, "submit")
    src = Path(mod.__class__.__module__.replace(".", "/") + ".py")
    # imported module path
    text = Path("/workspace/botmoduleproject1/modules/pm7_persistence/module.py").read_text()
    assert "MetaTrader" not in text
    assert "submit(" not in text


def test_no_telegram_import():
    import botmoduleproject1.modules.pm7_persistence as pkg
    import sys
    assert not any("telegram" in m for m in sys.modules if m.startswith("botmoduleproject1.modules.pm7"))


def test_publication_forbids_broker_truth():
    with pytest.raises(Exception):
        PersistencePublicationBundle.model_validate(
            {"occurred_at": AS_OF, "mode": "memory", "mt5_used": True}
        )
    with pytest.raises(Exception):
        PersistencePublicationBundle.model_validate(
            {"occurred_at": AS_OF, "mode": "memory", "broker_side_effect": True}
        )


def test_no_hidden_purge():
    mod = pm7_module()
    mod.ingest(make_event())
    _status, why = mod.purge()
    assert why != "purged"
    assert len(mod.journal.records()) == 1
