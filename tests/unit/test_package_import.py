"""Sequence 00: package imports and safety defaults."""

from botmoduleproject1 import (
    DEFAULT_TRADING_MODE,
    LIVE_TRADING_ENABLED_DEFAULT,
    __version__,
)


def test_version_is_sequence_zero() -> None:
    assert __version__ == "0.0.0"


def test_live_trading_disabled_by_default() -> None:
    assert LIVE_TRADING_ENABLED_DEFAULT is False


def test_default_mode_is_demo() -> None:
    assert DEFAULT_TRADING_MODE == "demo"
