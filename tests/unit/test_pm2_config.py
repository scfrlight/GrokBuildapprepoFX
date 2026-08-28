"""PM2 config validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config


def test_empty_universe_rejected() -> None:
    with pytest.raises(ValidationError):
        Pm2Config(universe=())


def test_duplicate_symbols_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        Pm2Config(universe=("EURUSD", "EURUSD"))


def test_unknown_timeframe_rejected() -> None:
    with pytest.raises(ValidationError, match="unsupported"):
        Pm2Config(timeframes=("M7",))


def test_symbols_normalized_upper() -> None:
    cfg = Pm2Config(universe=("eurusd", " gbpusd "))
    assert cfg.universe == ("EURUSD", "GBPUSD")
