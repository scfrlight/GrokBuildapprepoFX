"""Immutable feature snapshot from confirmed bars."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.pm2 import FeatureFamily
from botmoduleproject1.modules.pm2_market_context.features.normalization import atr, closes, roc, sma


class FeatureSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    as_of: datetime
    timeframe: Timeframe
    bars: int
    close: float
    sma_fast: float
    sma_slow: float
    roc_n: float
    atr: float
    atr_pct: float
    family_raw: dict[str, float] = Field(default_factory=dict)
    provenance: dict[str, str] = Field(default_factory=dict)


def build_snapshot(
    symbol: str,
    timeframe: Timeframe,
    bars: tuple[OhlcvBar, ...],
    as_of: datetime,
) -> FeatureSnapshot:
    px = closes(bars)
    last = px[-1] if px else 0.0
    fast = sma(px, 8)
    slow = sma(px, 21)
    rate = roc(px, 8)
    range_atr = atr(bars, 14)
    atr_pct = (range_atr / last) if last else 0.0
    trend = 0.0 if slow == 0 else (fast - slow) / abs(slow)
    family = {
        FeatureFamily.DIRECTIONAL_BIAS.value: trend,
        FeatureFamily.MOMENTUM.value: rate,
        FeatureFamily.VOLATILITY.value: atr_pct,
    }
    return FeatureSnapshot(
        symbol=symbol,
        as_of=as_of,
        timeframe=timeframe,
        bars=len(bars),
        close=last,
        sma_fast=fast,
        sma_slow=slow,
        roc_n=rate,
        atr=range_atr,
        atr_pct=atr_pct,
        family_raw=family,
        provenance={
            "source": "synthetic_confirmed_bars",
            "feature_set_version": "pm2.features.v1",
            "timeframe": timeframe.value,
        },
    )


def snapshot_dict(snap: FeatureSnapshot) -> dict[str, Any]:
    return snap.model_dump(mode="json")
