"""Typed PM3-Strategy Engine configuration. No secrets. No order-send knobs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from botmoduleproject1.contracts.v1.strategy_engine import StrategyTemplateType


class ConsensusWeights(BaseModel):
    historical_reliability: float = Field(default=0.35, ge=0.0, le=1.0)
    regime_fit: float = Field(default=0.25, ge=0.0, le=1.0)
    setup_quality: float = Field(default=0.20, ge=0.0, le=1.0)
    friction_fit: float = Field(default=0.10, ge=0.0, le=1.0)
    recent_live_health: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _sum(self) -> ConsensusWeights:
        total = (
            self.historical_reliability
            + self.regime_fit
            + self.setup_quality
            + self.friction_fit
            + self.recent_live_health
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"consensus weights must sum to 1.0, got {total}")
        return self


class ConsensusThresholds(BaseModel):
    go_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    edge_margin: float = Field(default=0.10, ge=0.0, le=1.0)
    min_selected_votes: int = Field(default=1, ge=1, le=3)
    conflict_no_trade: float = Field(default=0.35, ge=0.0, le=1.0)


class Pm3StrategyEngineConfig(BaseModel):
    universe: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
    operating_mode: str = "shadow"
    max_active_branches: int = Field(default=3, ge=1, le=3)
    require_handoff_eligibility: bool = True
    enabled_templates: tuple[str, ...] = (
        StrategyTemplateType.TREND_PULLBACK.value,
        StrategyTemplateType.ORB_SESSION_BREAKOUT.value,
        StrategyTemplateType.MEAN_REVERSION.value,
    )
    disabled_templates: tuple[str, ...] = (
        StrategyTemplateType.LIQUIDITY_SWEEP_REVERSAL.value,
        StrategyTemplateType.VOLATILITY_SQUEEZE_BREAKOUT.value,
    )
    weights: ConsensusWeights = Field(default_factory=ConsensusWeights)
    thresholds: ConsensusThresholds = Field(default_factory=ConsensusThresholds)
    calibration_policy: str = "reliability_table"
    stale_ttl_hours: int = Field(default=4, ge=1, le=48)
    signal_expiry_hours: int = Field(default=4, ge=1, le=48)
    observe_only: bool = True
    audit_events: bool = True
    require_feature_flag: bool = True

    @field_validator("universe")
    @classmethod
    def _uni(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(s.strip().upper() for s in value if s.strip())
        if not cleaned:
            raise ValueError("universe must not be empty")
        return cleaned

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value not in {"shadow", "observe-only", "paper"}:
            raise ValueError("operating_mode must be shadow|observe-only|paper")
        return value

    @model_validator(mode="after")
    def _no_execution_knobs(self) -> Pm3StrategyEngineConfig:
        overlap = set(self.enabled_templates) & set(self.disabled_templates)
        if overlap:
            raise ValueError(f"templates both enabled and disabled: {overlap}")
        return self


def config_from_settings(settings: object) -> Pm3StrategyEngineConfig:
    section = getattr(settings, "pm3_strategy_engine")
    return Pm3StrategyEngineConfig(
        universe=tuple(section.universe),
        operating_mode=section.operating_mode,
        max_active_branches=section.max_active_branches,
        require_handoff_eligibility=section.require_handoff_eligibility,
        enabled_templates=tuple(section.enabled_templates),
        thresholds=ConsensusThresholds(
            go_threshold=section.go_threshold,
            edge_margin=section.edge_margin,
            min_selected_votes=section.min_selected_votes,
            conflict_no_trade=section.conflict_no_trade,
        ),
        stale_ttl_hours=section.stale_ttl_hours,
    )
