from botmoduleproject1.contracts.v1.operator import CommandDisposition
from botmoduleproject1.contracts.v1.roles import OperatorRole
from botmoduleproject1.contracts.v1.tuning import TuningChangeStatus
from botmoduleproject1.modules.pm8_operator.config.schema import Pm8OperatorConfig
from tests.unit.pm8_support import actor, pm8_module


def test_studio_never_auto_promotes():
    mod = pm8_module()
    r = mod.handle_text("/propose go_threshold 0.6", actor(OperatorRole.OPERATOR, "op"))
    assert r.disposition is CommandDisposition.ACCEPTED
    assert r.details["auto_promote_to_live"] is False
    prop = mod.studio.snapshot()[0]
    assert prop.auto_promote_to_live is False
    assert prop.status is TuningChangeStatus.PROPOSED


def test_studio_disabled_refuses():
    mod = pm8_module(config=Pm8OperatorConfig(studio_enabled=False))
    r = mod.handle_text("/propose go_threshold 0.6", actor(OperatorRole.OPERATOR, "op"))
    assert r.disposition is CommandDisposition.REFUSED
    assert r.reason_code == "studio_disabled"


def test_config_rejects_auto_promote():
    try:
        Pm8OperatorConfig(auto_promote_to_live=True)
        raise AssertionError("should have refused")
    except Exception as exc:
        assert "auto-promote" in str(exc).lower() or "auto_promote" in str(exc)
