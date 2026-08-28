"""Market adapters. Sequence 03 ships a synthetic confirmed-bar feed only."""

from botmoduleproject1.adapters.market.synthetic import SyntheticMarketFeed, generate_bars

__all__ = ["SyntheticMarketFeed", "generate_bars"]
