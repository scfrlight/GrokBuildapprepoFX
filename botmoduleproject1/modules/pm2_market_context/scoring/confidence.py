"""Confidence from evidence agreement and data quality."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


def confidence_score(
    *,
    regime_confidence: float,
    momentum_stability: float,
    quality: DataQualityStatus,
    veto_count: int,
) -> float:
    base = 55.0 * regime_confidence + 35.0 * momentum_stability
    if quality is DataQualityStatus.DEGRADED:
        base -= 15
    if quality is DataQualityStatus.STALE:
        base -= 30
    base -= veto_count * 12
    return clamp(base)
