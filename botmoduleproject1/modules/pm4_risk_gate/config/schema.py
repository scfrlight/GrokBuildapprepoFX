"""Typed PM4 risk-gate configuration. No secrets. No order-send knobs."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


def _pct(value: Decimal, name: str) -> Decimal:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


class Pm4RiskGateConfig(BaseModel):
    """Public knobs. Enabling the gate is a feature flag, not this block."""

    operating_mode: str = "shadow"
    observe_only: bool = True
    account_equity: Decimal = Field(default=Decimal("100000"), gt=0)
    account_currency: str = "USD"
    contract_size: Decimal = Field(default=Decimal("100000"), gt=0)
    lot_step: Decimal = Field(default=Decimal("0.01"), gt=0)
    min_lots: Decimal = Field(default=Decimal("0.01"), gt=0)
    max_lots: Decimal = Field(default=Decimal("5.0"), gt=0)

    account_risk_pct: Decimal = Field(default=Decimal("0.020"))
    sleeve_risk_pct: Decimal = Field(default=Decimal("0.010"))
    regime_risk_pct: Decimal = Field(default=Decimal("0.008"))
    symbol_risk_pct: Decimal = Field(default=Decimal("0.005"))
    cluster_risk_pct: Decimal = Field(default=Decimal("0.010"))
    candidate_risk_pct: Decimal = Field(default=Decimal("0.005"))
    max_per_trade_risk_pct: Decimal = Field(default=Decimal("0.005"))
    max_open_risk_pct: Decimal = Field(default=Decimal("0.020"))
    max_intraday_loss_pct: Decimal = Field(default=Decimal("0.015"))
    max_daily_loss_pct: Decimal = Field(default=Decimal("0.020"))

    heat_warm: Decimal = Field(default=Decimal("0.008"))
    heat_hot: Decimal = Field(default=Decimal("0.014"))
    heat_critical: Decimal = Field(default=Decimal("0.018"))
    max_effective_heat: Decimal = Field(default=Decimal("0.020"))

    dd_mild: Decimal = Field(default=Decimal("0.020"))
    dd_reduced: Decimal = Field(default=Decimal("0.040"))
    dd_restricted: Decimal = Field(default=Decimal("0.060"))
    dd_freeze: Decimal = Field(default=Decimal("0.080"))
    dd_kill: Decimal = Field(default=Decimal("0.100"))
    losing_streak_throttle: int = Field(default=4, ge=1)

    cluster_cap: Decimal = Field(default=Decimal("0.012"))
    usd_concentration_cap: Decimal = Field(default=Decimal("0.015"))
    european_basket_cap: Decimal = Field(default=Decimal("0.012"))
    crowding_block: Decimal = Field(default=Decimal("0.80"))
    one_per_cluster: bool = True

    stale_ttl_seconds: int = Field(default=14400, ge=60, le=172800)
    min_forecast_samples: int = Field(default=20, ge=1)
    wide_interval_pct: Decimal = Field(default=Decimal("0.008"))
    min_liquidity_score: float = Field(default=40.0, ge=0.0, le=100.0)
    min_stop_distance: Decimal = Field(default=Decimal("0.00010"), gt=0)
    max_stop_distance: Decimal = Field(default=Decimal("0.05000"), gt=0)
    price_collar_bps: Decimal = Field(default=Decimal("50"))
    max_notional: Decimal = Field(default=Decimal("500000"), gt=0)
    burst_limit: int = Field(default=8, ge=1)
    burst_window_seconds: int = Field(default=60, ge=1)
    duplicate_ttl_seconds: int = Field(default=86400, ge=1)
    verdict_ttl_seconds: int = Field(default=3600, ge=60)

    session_allow: tuple[str, ...] = ("london", "new_york", "overlap", "asia")
    risk_reducing_only_on_kill: bool = True
    recovery_cooldown_seconds: int = Field(default=300, ge=1)
    require_manual_recovery_after_kill: bool = True
    auto_rearm: bool = False
    telemetry_verbose: bool = True
    cancel_on_disconnect: bool = True
    route_name: str = "pm5_pending"

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        allowed = {"shadow", "observe-only", "paper"}
        if value not in allowed:
            raise ValueError("operating_mode must be shadow|observe-only|paper")
        return value

    @field_validator(
        "account_risk_pct",
        "sleeve_risk_pct",
        "regime_risk_pct",
        "symbol_risk_pct",
        "cluster_risk_pct",
        "candidate_risk_pct",
        "max_per_trade_risk_pct",
        "max_open_risk_pct",
        "max_intraday_loss_pct",
        "max_daily_loss_pct",
        "heat_warm",
        "heat_hot",
        "heat_critical",
        "max_effective_heat",
        "dd_mild",
        "dd_reduced",
        "dd_restricted",
        "dd_freeze",
        "dd_kill",
        "cluster_cap",
        "usd_concentration_cap",
        "european_basket_cap",
        "crowding_block",
        "wide_interval_pct",
    )
    @classmethod
    def _bounded(cls, value: Decimal, info) -> Decimal:  # type: ignore[no-untyped-def]
        return _pct(value, info.field_name)

    @model_validator(mode="after")
    def _invariants(self) -> Pm4RiskGateConfig:
        if self.auto_rearm:
            raise ValueError("auto_rearm must stay false; kill-switch has no hidden rearm")
        if self.min_lots > self.max_lots:
            raise ValueError("min_lots must be <= max_lots")
        if self.dd_mild > self.dd_reduced > self.dd_restricted > self.dd_freeze > self.dd_kill:
            raise ValueError("drawdown ladder must be non-decreasing")
        if self.dd_mild > self.dd_reduced > self.dd_restricted > self.dd_freeze > self.dd_kill:
            raise ValueError("drawdown ladder must be non-decreasing")
        if not (
            self.dd_mild
            <= self.dd_reduced
            <= self.dd_restricted
            <= self.dd_freeze
            <= self.dd_kill
        ):
            raise ValueError("drawdown thresholds must be ordered mild<=reduced<=restricted<=freeze<=kill")
        if not (self.heat_warm <= self.heat_hot <= self.heat_critical <= self.max_effective_heat):
            raise ValueError("heat thresholds must be ordered warm<=hot<=critical<=max")
        return self


def config_from_settings(settings: object) -> Pm4RiskGateConfig:
    section = getattr(settings, "pm4_risk_gate", None)
    if section is None:
        return Pm4RiskGateConfig()
    payload = section.model_dump() if hasattr(section, "model_dump") else dict(section)
    allowed = set(Pm4RiskGateConfig.model_fields)
    return Pm4RiskGateConfig(**{k: v for k, v in payload.items() if k in allowed})
