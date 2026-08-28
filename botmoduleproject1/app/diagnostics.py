"""Startup diagnostics snapshot — human and machine readable. Secrets redacted."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.secrets import redact_node
from botmoduleproject1.app.settings import Settings
from botmoduleproject1.contracts.v1.time import utc_now


class DiagnosticsSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_name: str
    environment: str
    cli_mode: str
    profile: str
    trading_mode: str
    live_trading_enabled: bool
    config_fingerprint: str
    lifecycle_state: str
    allowed_capabilities: tuple[str, ...] = ()
    forbidden_operations: tuple[str, ...] = ()
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    modules: dict[str, Any] = Field(default_factory=dict)
    health: dict[str, Any] = Field(default_factory=dict)
    preflight: dict[str, Any] = Field(default_factory=dict)
    captured_at: str

    def banner_lines(self) -> list[str]:
        caps = ", ".join(self.allowed_capabilities) or "(none)"
        return [
            f"{self.app_name} platform kernel",
            (
                f"environment={self.environment} cli_mode={self.cli_mode} "
                f"profile={self.profile} trading_mode={self.trading_mode}"
            ),
            f"live_trading_enabled={self.live_trading_enabled}",
            f"allowed_capabilities={caps}",
            f"config_fingerprint={self.config_fingerprint}",
            f"lifecycle={self.lifecycle_state}",
            f"modules={', '.join(self.modules) or '(none)'}",
            f"captured_at={self.captured_at}",
            "NOT TRADE READY. Live trading is disabled. No orders will be sent.",
        ]


def build_snapshot(
    settings: Settings,
    *,
    state: LifecycleState,
    modules: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
) -> DiagnosticsSnapshot:
    policy = settings.profile_policy
    return DiagnosticsSnapshot(
        app_name=settings.app.name,
        environment=settings.app.environment,
        cli_mode=settings.cli_mode,
        profile=settings.profile.value,
        trading_mode=settings.safety.trading_mode,
        live_trading_enabled=settings.safety.live_trading_enabled,
        config_fingerprint=settings.fingerprint(),
        lifecycle_state=state.value,
        allowed_capabilities=tuple(c.value for c in policy.allowed_capabilities),
        forbidden_operations=policy.forbidden_operations,
        feature_flags=settings.feature_flags.enabled_map(),
        modules=modules or {},
        health=redact_node(health or {}),
        preflight=redact_node(preflight or {}),
        captured_at=utc_now().isoformat(),
    )
