from botmoduleproject1.adapters.telegram import RealTelegramTransport, decode_update, encode_receipt
from botmoduleproject1.app.exceptions import FeatureFlagError
from botmoduleproject1.contracts.v1.operator import CommandDisposition, TransportMode
from botmoduleproject1.modules.pm8_operator.config.schema import Pm8OperatorConfig
from tests.unit.pm8_support import actor, pm8_module


def test_simulated_transport_no_network():
    mod = pm8_module()
    r = mod.handle_text("/health", actor())
    assert r.disposition is CommandDisposition.ACCEPTED
    assert mod.transport_mode is TransportMode.SIMULATED
    assert mod.transport.outbox
    assert "mt5=false" in mod.transport.outbox[-1].text


def test_telegram_decode_encode_has_no_orders():
    inbound = decode_update(
        {
            "update_id": 7,
            "message": {
                "date": 1_700_000_000,
                "text": "/status",
                "chat": {"id": 99},
                "from": {"id": 42, "username": "desk"},
            },
        }
    )
    assert inbound.text == "/status"
    assert inbound.user_id == "42"
    mod = pm8_module()
    receipt = mod.handle_text(inbound.text, actor(), idempotency_key="tg-1")
    outbound = encode_receipt(receipt, chat_id=inbound.chat_id)
    assert "place" not in outbound.text.lower()
    assert receipt.creates_order is False


def test_real_telegram_refused():
    try:
        RealTelegramTransport()
        raise AssertionError("must refuse")
    except FeatureFlagError as exc:
        assert "Sequence 10" in str(exc)


def test_telegram_api_mode_refused_in_config():
    try:
        Pm8OperatorConfig(operating_mode="telegram_api")
        raise AssertionError("must refuse")
    except Exception as exc:
        assert "telegram_api" in str(exc)
