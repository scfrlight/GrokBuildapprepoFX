"""Startup and platform exceptions. Fail closed; never trade through these."""

from __future__ import annotations


class PlatformError(Exception):
    """Base platform error."""


class LiveTradingDisabledError(PlatformError):
    """Raised when live trading is requested. Recognition is not permission."""

    def __init__(self, reason: str = "LIVE_TRADING_ENABLED=true or mode=live") -> None:
        message = (
            "LIVE TRADING IS DISABLED.\n"
            f"Refusing to start because {reason}.\n"
            "This build is demo-first. See docs/architecture/runtime_modes.md and ADR-002."
        )
        super().__init__(message)
        self.reason = reason


class SettingsError(PlatformError):
    """Invalid or incomplete configuration."""


class RegistryError(PlatformError):
    """Module registry rejected a registration or lookup."""


class LifecycleError(PlatformError):
    """Illegal lifecycle transition."""


class HealthError(PlatformError):
    """Critical startup or readiness check failed."""


class ExecutionDisabledError(PlatformError):
    """Any attempt to send an order through the Sequence 01 kernel."""
