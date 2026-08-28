"""Startup diagnostics snapshot — human and machine readable."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.settings import Settings
from botmoduleproject1.contracts.v1.time import utc_now


class DiagnosticsSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_name: str
    environment: str
    cli_mode: str
    trading_mode: str
    live_trading_enabled: bool
    config_fingerprint: str
    lifecycle_state: str
    modules: dict[str, Any] = Field(default_factory=dict)
    health: dict[str, Any] = Field(default_factory=dict)
    captured_at: str

    def banner_lines(self) -> list[str]:
        return [
            f"{self.app_name} platform kernel",
            f"environment={self.environment} cli_mode={self.cli_mode} trading_mode={self.trading_mode}",
            f"live_trading_enabled={self.live_trading_enabled}",
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
) -> DiagnosticsSnapshot:
    return DiagnosticsSnapshot(
        app_name=settings.app.name,
        environment=settings.app.environment,
        cli_mode=settings.cli_mode,
        trading_mode=settings.safety.trading_mode,
        live_trading_enabled=settings.safety.live_trading_enabled,
        config_fingerprint=settings.fingerprint(),
        lifecycle_state=state.value,
        modules=modules or {},
        health=health or {},
        captured_at=utc_now().isoformat(),
    )
