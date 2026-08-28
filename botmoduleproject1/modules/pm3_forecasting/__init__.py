"""PM3 forecasting / QRF.

Research-to-inference pipeline. Residual quantile envelope (not a fitted QRF).
Enriches uncertainty. Never creates a TradeIntent, never mutates side, never orders.
"""

from botmoduleproject1.modules.pm3_forecasting.module import PM3ForecastingModule

__all__ = ["PM3ForecastingModule"]
