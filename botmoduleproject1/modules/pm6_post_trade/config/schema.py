"""PM6 knobs. Enabling is a feature flag, not this block."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class Pm6PostTradeConfig(BaseModel):
    operating_mode: str = "shadow"
    observe_only: bool = True
    freshness_ttl_seconds: int = Field(default=300, ge=1)
    stale_ttl_seconds: int = Field(default=14400, ge=60)
    alert_dedup_seconds: int = Field(default=60, ge=1)
    incident_correlation_seconds: int = Field(default=300, ge=1)
    submit_burst: int = Field(default=8, ge=1)
    reject_burst: int = Field(default=6, ge=1)
    cancel_burst: int = Field(default=12, ge=1)
    fill_burst: int = Field(default=8, ge=1)
    burst_window_seconds: int = Field(default=60, ge=1)
    silence_seconds: int = Field(default=600, ge=1)
    quantity_drift_bps: int = Field(default=0, ge=0)
    escalation_critical_seconds: int = Field(default=0, ge=0)
    escalation_high_seconds: int = Field(default=300, ge=0)
    require_withdrawal_approval: bool = True
    require_withdrawal_confirmation: bool = True
    auto_rearm: bool = False
    auto_complete_withdrawal: bool = False
    mt5_enabled: bool = False
    broker_commands: bool = False
    durable: bool = False
    telemetry_verbose: bool = True
    surveillance_enabled: bool = True
    incident_response_enabled: bool = True
    governance_enabled: bool = True
    withdrawal_planner_enabled: bool = True

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value not in {"disabled", "shadow", "observe"}:
            raise ValueError("operating_mode must be disabled|shadow|observe")
        return value

    @model_validator(mode="after")
    def _invariants(self) -> Pm6PostTradeConfig:
        if self.auto_rearm:
            raise ValueError("auto_rearm must stay false")
        if self.mt5_enabled:
            raise ValueError("PM6 cannot enable MT5")
        if self.broker_commands:
            raise ValueError("PM6 cannot issue broker commands")
        if self.durable:
            raise ValueError("PM6 is non-durable before PM7")
        if self.auto_complete_withdrawal:
            raise ValueError("withdrawal cannot auto-complete")
        return self


def config_from_settings(settings: object) -> Pm6PostTradeConfig:
    section = getattr(settings, "pm6_post_trade", None)
    if section is None:
        return Pm6PostTradeConfig()
    payload = section.model_dump() if hasattr(section, "model_dump") else dict(section)
    allowed = set(Pm6PostTradeConfig.model_fields)
    return Pm6PostTradeConfig(**{k: v for k, v in payload.items() if k in allowed})
