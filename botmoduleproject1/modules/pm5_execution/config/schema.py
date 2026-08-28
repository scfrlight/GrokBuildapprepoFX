"""PM5 knobs. Enabling is a feature flag, not this block. No live mode."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class Pm5ExecutionConfig(BaseModel):
    operating_mode: str = "disabled"
    observe_only: bool = True
    allowed_order_types: tuple[str, ...] = ("market", "limit")
    symbol_allowlist: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
    execution_policy: str = "simulation_only"
    stale_ttl_seconds: int = Field(default=14400, ge=60)
    idempotency_ttl_seconds: int = Field(default=86400, ge=1)
    submit_timeout_ms: int = Field(default=5000, ge=1)
    max_retries: int = Field(default=2, ge=0, le=5)
    submit_burst: int = Field(default=8, ge=1)
    reject_burst: int = Field(default=6, ge=1)
    cancel_burst: int = Field(default=12, ge=1)
    modify_burst: int = Field(default=8, ge=1)
    burst_window_seconds: int = Field(default=60, ge=1)
    recovery_cooldown_seconds: int = Field(default=300, ge=1)
    require_manual_recovery: bool = True
    auto_rearm: bool = False
    broker_adapter_enabled: bool = False
    mt5_enabled: bool = False
    simulation_auto_fill: bool = True
    slippage_limit: Decimal = Field(default=Decimal("0.00050"))
    cancel_on_disconnect: bool = True
    telemetry_verbose: bool = True

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        allowed = {"disabled", "shadow", "simulation"}
        if value not in allowed:
            raise ValueError("operating_mode must be disabled|shadow|simulation in Sequence 07")
        return value

    @model_validator(mode="after")
    def _invariants(self) -> Pm5ExecutionConfig:
        if self.auto_rearm:
            raise ValueError("auto_rearm must stay false")
        if self.broker_adapter_enabled:
            raise ValueError("broker adapter cannot be enabled in Sequence 07")
        if self.mt5_enabled:
            raise ValueError("mt5 cannot be enabled in Sequence 07")
        if self.max_retries > 5:
            raise ValueError("unsafe retry count")
        return self


def config_from_settings(settings: object) -> Pm5ExecutionConfig:
    section = getattr(settings, "pm5_execution", None)
    if section is None:
        return Pm5ExecutionConfig()
    payload = section.model_dump() if hasattr(section, "model_dump") else dict(section)
    allowed = set(Pm5ExecutionConfig.model_fields)
    return Pm5ExecutionConfig(**{k: v for k, v in payload.items() if k in allowed})
