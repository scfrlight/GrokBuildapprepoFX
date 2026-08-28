from datetime import datetime

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.strategy import (
    ConsensusDecision,
    Direction,
    EntryType,
    TradeIntent,
)
from botmoduleproject1.contracts.v1.time import UTC, utc_now


def test_trade_intent_rejects_lot_size() -> None:
    with pytest.raises(ValidationError, match="lot size"):
        TradeIntent(
            idempotency_key="k",
            occurred_at=utc_now(),
            symbol="EURUSD",
            direction=Direction.BUY,
            entry_type=EntryType.MARKET,
            requested_volume="0.01",
        )


def test_trade_intent_new_fields_default() -> None:
    intent = TradeIntent(
        idempotency_key="k2",
        occurred_at=utc_now(),
        symbol="EURUSD",
        direction=Direction.BUY,
        entry_type=EntryType.LIMIT,
    )
    assert intent.requested_volume is None
    assert intent.producer == "pm3_strategy_engine"
    assert ConsensusDecision.GO_LONG.value == "go_long"


def test_naive_created_at_rejected() -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        TradeIntent(
            idempotency_key="k3",
            occurred_at=utc_now(),
            created_at=naive,
            symbol="EURUSD",
            direction=Direction.BUY,
            entry_type=EntryType.MARKET,
        )
