"""Bar freshness / completeness. Fail closed to stale when unknown."""

from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus

_TF_MINUTES = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.M30: 30,
    Timeframe.H1: 60,
    Timeframe.H4: 240,
    Timeframe.D1: 1440,
    Timeframe.W1: 10080,
}


def classify(
    bars: tuple[OhlcvBar, ...],
    timeframe: Timeframe,
    as_of: datetime,
    *,
    stale_after_bars: int = 3,
) -> DataQualityStatus:
    if not bars:
        return DataQualityStatus.INCOMPLETE
    last = bars[-1]
    if last.high < last.low:
        return DataQualityStatus.MALFORMED
    minutes = _TF_MINUTES[timeframe]
    end = last.broker_as_of or (last.open_time + timedelta(minutes=minutes))
    age = as_of - end
    if age > timedelta(minutes=minutes * stale_after_bars):
        return DataQualityStatus.STALE
    if len(bars) < 16:
        return DataQualityStatus.INCOMPLETE
    return DataQualityStatus.OK
