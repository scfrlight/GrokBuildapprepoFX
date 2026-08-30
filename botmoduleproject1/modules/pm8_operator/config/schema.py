"""PM8 knobs. Enabling is a feature flag, not this block."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class Pm8OperatorConfig(BaseModel):
    operating_mode: str = "simulated"
    observe_only: bool = True
    approval_ttl_seconds: int = Field(default=900, ge=30, le=86400)
    halt_requires_dual_control: bool = False
    allow_purge: bool = False
    mt5_enabled: bool = False
    broker_commands: bool = False
    telegram_api: bool = False
    auto_rearm: bool = False
    auto_promote_to_live: bool = False
    telemetry_verbose: bool = True
    hitl_enabled: bool = True
    studio_enabled: bool = False
    audit_enabled: bool = True
    query_limit: int = Field(default=20, ge=1, le=100)
    allowlisted_user_ids: tuple[str, ...] = ()

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value == "telegram_api":
            raise ValueError("telegram_api transport is refused in Sequence 13")
        if value not in {"disabled", "simulated"}:
            raise ValueError("operating_mode must be disabled|simulated")
        return value

    @model_validator(mode="after")
    def _invariants(self) -> "Pm8OperatorConfig":
        if self.auto_rearm:
            raise ValueError("auto_rearm must stay false")
        if self.mt5_enabled:
            raise ValueError("PM8 cannot enable MT5")
        if self.broker_commands:
            raise ValueError("PM8 cannot issue broker commands")
        if self.telegram_api:
            raise ValueError("Telegram Bot API is refused in Sequence 13")
        if self.auto_promote_to_live:
            raise ValueError("studio cannot auto-promote to live")
        if self.allow_purge:
            raise ValueError("destructive purge is refused")
        return self


def config_from_settings(settings: object) -> Pm8OperatorConfig:
    section = getattr(settings, "pm8_operator", None)
    flags = getattr(settings, "feature_flags", None)
    data: dict = {}
    if section is not None:
        data = section.model_dump() if hasattr(section, "model_dump") else dict(section)
    if flags is not None:
        data["hitl_enabled"] = bool(getattr(flags, "pm8_hitl", True))
        data["studio_enabled"] = bool(getattr(flags, "fine_tune_studio", False))
        data["audit_enabled"] = bool(getattr(flags, "pm8_command_audit", True))
    return Pm8OperatorConfig.model_validate(data)
