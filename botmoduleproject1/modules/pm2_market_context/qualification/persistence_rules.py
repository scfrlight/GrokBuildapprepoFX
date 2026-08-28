"""Persistence thresholds for qualification."""

from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Thresholds


def required_bars(thresholds: Pm2Thresholds) -> int:
    return thresholds.persistence_bars
