"""Composition root. The only place that binds adapters to ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from botmoduleproject1.adapters.clock.system import FakeClock, SystemClock
from botmoduleproject1.app.capabilities import PLATFORM_CORE
from botmoduleproject1.app.contracts import ClockPort
from botmoduleproject1.app.health import HealthAggregator
from botmoduleproject1.app.lifecycle import LifecycleManager
from botmoduleproject1.app.logging_config import configure_logging, get_logger
from botmoduleproject1.app.registry import ModuleRegistry
from botmoduleproject1.app.settings import Settings
from botmoduleproject1.app.stubs import (
    DisabledExecution,
    NullMarketData,
    NullModel,
    NullMonitoring,
    NullNotifications,
    NullRiskGate,
    NullSignals,
    NullStorage,
    PlatformHealth,
)


@dataclass
class Container:
    settings: Settings
    clock: ClockPort
    registry: ModuleRegistry
    health: HealthAggregator
    lifecycle: LifecycleManager
    extras: dict[str, Any] = field(default_factory=dict)

    def logger(self, name: str = "botmoduleproject1"):
        return get_logger(name)


def build_container(
    settings: Settings,
    *,
    overrides: dict[str, Any] | None = None,
) -> Container:
    configure_logging(settings)
    overrides = dict(overrides or {})
    clock: ClockPort
    if "clock" in overrides:
        clock = overrides["clock"]
    elif settings.clock.source == "fake":
        clock = FakeClock()
    else:
        clock = SystemClock()

    registry = overrides.get("registry") or ModuleRegistry(settings.modules)
    health = overrides.get("health") or HealthAggregator()
    lifecycle = overrides.get("lifecycle") or LifecycleManager()

    builtins = [
        overrides.get("platform") or PlatformHealth(),
        overrides.get("market_data") or NullMarketData(),
        overrides.get("signals") or NullSignals(),
        overrides.get("forecasting") or NullModel(),
        overrides.get("risk") or NullRiskGate(),
        overrides.get("execution") or DisabledExecution(),
        overrides.get("storage") or NullStorage(),
        overrides.get("notifications") or NullNotifications(),
        overrides.get("monitoring") or NullMonitoring(),
    ]

    # Always ensure platform metadata is known even if caller replaced instance.
    if not any(getattr(m, "metadata", lambda: None)().name == PLATFORM_CORE.name for m in builtins if hasattr(m, "metadata")):
        builtins.insert(0, PlatformHealth())

    for module in builtins:
        meta_fn = getattr(module, "metadata", None)
        if meta_fn is None:
            continue
        registry.register(meta_fn(), module)
        health.add(module)

    registry.validate_dependencies()
    return Container(
        settings=settings,
        clock=clock,
        registry=registry,
        health=health,
        lifecycle=lifecycle,
        extras=overrides,
    )
