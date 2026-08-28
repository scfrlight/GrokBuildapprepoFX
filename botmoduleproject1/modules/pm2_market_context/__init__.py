"""PM2 Market Context Engine.

Ranking and candidate-qualification layer. Does not send orders, size
positions, or run QRF/ML. HMM/GMM adapters exist as disabled stubs.
"""

from botmoduleproject1.modules.pm2_market_context.capabilities import PM2_METADATA
from botmoduleproject1.modules.pm2_market_context.module import PM2Module

__all__ = ["PM2_METADATA", "PM2Module"]
