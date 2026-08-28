"""PM3-Strategy Engine.

Replaceable strategy operating platform. Emits TradeIntent / NoTradeDecision.
Never shortened to “PM3”. Not forecasting/QRF. Not execution.
"""

from botmoduleproject1.modules.pm3_strategy_engine.module import PM3StrategyEngineModule

__all__ = ["PM3StrategyEngineModule"]
