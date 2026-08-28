from pathlib import Path

import pytest

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import ExecutionDisabledError, LiveTradingDisabledError
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution, NullMonitoring
from botmoduleproject1.contracts.v1.post_trade import OperationalTruthBundle, TruthSource
from botmoduleproject1.modules.pm6_post_trade.module import PM6PostTradeModule
from tests.unit.pm6_support import observe_allow, pm6_module

ROOT = Path(__file__).resolve().parents[2]


def test_flags_default_false() -> None:
    settings = load_settings(config_path=ROOT / "configs" / "base.example.yaml", environ={})
    assert settings.feature_flags.pm6_post_trade is False
    assert settings.feature_flags.pm6_surveillance is False
    container = build_container(settings)
    assert isinstance(container.registry.get("pm6_monitoring").instance, NullMonitoring)


def test_live_profile_blocked() -> None:
    with pytest.raises(LiveTradingDisabledError):
        load_settings(config_path=ROOT / "configs" / "base.example.yaml", profile="live", environ={})


def test_cannot_enable_mt5_via_config() -> None:
    with pytest.raises(Exception):
        load_settings(
            config_path=ROOT / "configs" / "base.example.yaml",
            environ={},
            extra={"pm6_post_trade": {"mt5_enabled": True}},
        )


def test_pm6_does_not_submit_orders() -> None:
    settings = load_settings(config_path=ROOT / "configs" / "test.example.yaml", environ={})
    container = build_container(settings)
    exe = container.registry.get("pm5_execution").instance
    assert isinstance(exe, DisabledExecution)
    from botmoduleproject1.contracts.v1.execution import OrderRequest
    from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
    from uuid import uuid4
    from decimal import Decimal
    from tests.unit.pm4_support import AS_OF

    req = OrderRequest(
        causation_id=uuid4(),
        idempotency_key="nope",
        occurred_at=AS_OF,
        intent_id=uuid4(),
        risk_verdict_id=uuid4(),
        symbol="EURUSD",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
        volume=Decimal("0.1"),
    )
    with pytest.raises(ExecutionDisabledError):
        exe.submit(req)


def test_publication_forbids_broker_truth() -> None:
    _pm6, _r, _p, truth = observe_allow(key="safe-pub")
    assert isinstance(truth, OperationalTruthBundle)
    payload = truth.model_dump()
    payload["truth_source"] = TruthSource.BROKER_TRUTH
    with pytest.raises(Exception):
        OperationalTruthBundle.model_validate(payload)
    payload = truth.model_dump()
    payload["mt5_used"] = True
    with pytest.raises(Exception):
        OperationalTruthBundle.model_validate(payload)
    payload = truth.model_dump()
    payload["durable"] = True
    with pytest.raises(Exception):
        OperationalTruthBundle.model_validate(payload)


def test_no_telegram_import() -> None:
    import botmoduleproject1.modules.pm6_post_trade.module as m

    src = Path(m.__file__).read_text(encoding="utf-8")
    assert "telegram" not in src.lower()


def test_no_metatrader_import() -> None:
    import sys

    import botmoduleproject1.modules.pm6_post_trade as pkg

    assert "MetaTrader5" not in sys.modules
    assert pkg.PM6PostTradeModule is PM6PostTradeModule
