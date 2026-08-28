"""Universe scan: pair-agnostic, confirmed bars, quality attached."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from botmoduleproject1.adapters.market.synthetic import SyntheticMarketFeed
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config
from botmoduleproject1.modules.pm2_market_context.scanner.freshness import classify


class SymbolSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    as_of: datetime
    quality: DataQualityStatus
    bars_by_tf: dict[str, tuple[OhlcvBar, ...]]
    eligible: bool


class UniverseScanner:
    def __init__(self, config: Pm2Config, feed: SyntheticMarketFeed) -> None:
        self.config = config
        self.feed = feed

    def scan(self, as_of: datetime) -> tuple[SymbolSnapshot, ...]:
        out: list[SymbolSnapshot] = []
        for symbol in self.config.universe:
            by_tf: dict[str, tuple[OhlcvBar, ...]] = {}
            qualities: list[DataQualityStatus] = []
            for raw_tf in self.config.timeframes:
                tf = Timeframe(raw_tf)
                series = self.feed.bars(symbol, tf)
                by_tf[raw_tf] = series
                qualities.append(
                    classify(series, tf, as_of, stale_after_bars=self.config.thresholds.stale_bars)
                )
            quality = DataQualityStatus.OK
            for item in qualities:
                if item is DataQualityStatus.MALFORMED:
                    quality = item
                    break
                if item is DataQualityStatus.STALE:
                    quality = item
                elif item is DataQualityStatus.INCOMPLETE and quality is DataQualityStatus.OK:
                    quality = item
            out.append(
                SymbolSnapshot(
                    symbol=symbol,
                    as_of=as_of,
                    quality=quality,
                    bars_by_tf=by_tf,
                    eligible=quality is DataQualityStatus.OK,
                )
            )
        return tuple(out)
