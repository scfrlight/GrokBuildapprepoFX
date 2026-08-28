"""PM2 configuration. Fail-fast on invalid values. No secrets."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from botmoduleproject1.modules.pm2_market_context.domain.enums import OperatingMode, RankingMode


class Pm2Weights(BaseModel):
    regime: float = Field(default=1.0, ge=0.0, le=2.0)
    directional_bias: float = Field(default=1.0, ge=0.0, le=2.0)
    structure: float = Field(default=0.9, ge=0.0, le=2.0)
    momentum: float = Field(default=0.85, ge=0.0, le=2.0)
    volatility: float = Field(default=0.7, ge=0.0, le=2.0)
    session_liquidity: float = Field(default=0.6, ge=0.0, le=2.0)
    correlation: float = Field(default=0.5, ge=0.0, le=2.0)
    macro: float = Field(default=0.0, ge=0.0, le=2.0)


class Pm2Thresholds(BaseModel):
    suppress_below: float = Field(default=40.0, ge=0.0, le=100.0)
    watch_below: float = Field(default=60.0, ge=0.0, le=100.0)
    eligible_below: float = Field(default=75.0, ge=0.0, le=100.0)
    high_below: float = Field(default=90.0, ge=0.0, le=100.0)
    persistence_bars: int = Field(default=2, ge=1, le=50)
    cooldown_bars: int = Field(default=4, ge=0, le=200)
    stale_bars: int = Field(default=3, ge=1, le=50)
    shortlist_size: int = Field(default=3, ge=1, le=20)
    watchlist_size: int = Field(default=5, ge=1, le=50)
    min_confidence: float = Field(default=35.0, ge=0.0, le=100.0)


class Pm2Config(BaseModel):
    universe: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
    timeframes: tuple[str, ...] = ("M15", "H1", "H4")
    decision_timeframe: str = "H1"
    lookback_bars: int = Field(default=64, ge=16, le=512)
    operating_mode: OperatingMode = OperatingMode.SHADOW
    ranking_mode: RankingMode = RankingMode.DETERMINISTIC
    one_per_cluster: bool = True
    ghost_tracking: bool = True
    telemetry: bool = True
    hmm_adapter: bool = False
    gmm_adapter: bool = False
    weights: Pm2Weights = Field(default_factory=Pm2Weights)
    thresholds: Pm2Thresholds = Field(default_factory=Pm2Thresholds)
    feature_set_version: str = "pm2.features.v1"

    @field_validator("universe")
    @classmethod
    def _universe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(s.strip().upper() for s in value if s.strip())
        if not cleaned:
            raise ValueError("pm2 universe must not be empty")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("pm2 universe contains duplicate symbols")
        return cleaned

    @field_validator("timeframes")
    @classmethod
    def _tfs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        allowed = {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}
        cleaned = tuple(s.strip().upper() for s in value)
        unknown = [s for s in cleaned if s not in allowed]
        if unknown:
            raise ValueError(f"unsupported timeframes: {unknown}")
        if not cleaned:
            raise ValueError("pm2 timeframes must not be empty")
        return cleaned


def config_from_settings(settings: object) -> Pm2Config:
    """Map Settings.pm2 public knobs onto the typed PM2 config."""
    section = getattr(settings, "pm2")
    return Pm2Config(
        universe=tuple(section.universe),
        timeframes=tuple(section.timeframes),
        decision_timeframe=section.decision_timeframe,
        lookback_bars=section.lookback_bars,
        operating_mode=OperatingMode(section.operating_mode),
        ranking_mode=RankingMode(section.ranking_mode),
        one_per_cluster=bool(section.one_per_cluster),
        ghost_tracking=bool(section.ghost_tracking),
        telemetry=bool(section.telemetry),
    )

