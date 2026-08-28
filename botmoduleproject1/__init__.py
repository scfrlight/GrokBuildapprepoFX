"""BotModuleProject1 platform kernel.

Sequence 03: PM2 market context (flag default-off).
Not trade-ready. Live trading is disabled. Python 3.11+ required.
"""

from botmoduleproject1.app.exceptions import LiveTradingDisabledError
from botmoduleproject1.app.settings import load_settings

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
