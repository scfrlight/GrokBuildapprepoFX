"""BotModuleProject1 platform kernel.

Not trade-ready. Live trading is disabled. Python 3.11+ required (ADR-008).
Heavy imports (settings/pydantic) are lazy so `python -m botmoduleproject1`
can fail-fast on an unsupported interpreter before those deps load.
"""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"
LIVE_TRADING_ENABLED_DEFAULT = False
DEFAULT_TRADING_MODE = "demo"

__all__ = [
    "DEFAULT_TRADING_MODE",
    "LIVE_TRADING_ENABLED_DEFAULT",
    "LiveTradingDisabledError",
    "__version__",
    "load_settings",
]


def __getattr__(name: str) -> Any:
    if name == "load_settings":
        from botmoduleproject1.app.settings import load_settings

        return load_settings
    if name == "LiveTradingDisabledError":
        from botmoduleproject1.app.exceptions import LiveTradingDisabledError

        return LiveTradingDisabledError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
