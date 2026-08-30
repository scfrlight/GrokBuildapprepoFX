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
    NullLedger,
    NullMarketData,
    NullModel,
    NullMonitoring,
    NullNotifications,
    NullOperator,
    NullRiskGate,
    NullSignals,
    NullStorage,
    PlatformHealth,
)


def _market_data_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "market_data" in overrides:
        return overrides["market_data"]
    if settings.feature_flags.market_data:
        from botmoduleproject1.modules.pm2_market_context.module import PM2Module

        return PM2Module.from_settings(settings, clock)
    return NullMarketData()


def _strategy_engine_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "signals" in overrides:
        return overrides["signals"]
    if settings.feature_flags.strategy_engine:
        from botmoduleproject1.modules.pm3_strategy_engine.module import PM3StrategyEngineModule

        return PM3StrategyEngineModule.from_settings(settings, clock)
    return NullSignals()


def _forecasting_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "forecasting" in overrides:
        return overrides["forecasting"]
    if settings.feature_flags.forecasting:
        from botmoduleproject1.modules.pm3_forecasting.module import PM3ForecastingModule

        return PM3ForecastingModule.from_settings(settings, clock)
    return NullModel()


def _risk_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "risk" in overrides:
        return overrides["risk"]
    if settings.feature_flags.risk_engine:
        from botmoduleproject1.modules.pm4_risk_gate.module import PM4RiskGateModule

        return PM4RiskGateModule.from_settings(settings, clock)
    return NullRiskGate()


def _execution_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "execution" in overrides:
        return overrides["execution"]
    if getattr(settings.feature_flags, "pm5_simulation", False):
        from botmoduleproject1.modules.pm5_execution.module import PM5ExecutionModule

        return PM5ExecutionModule.from_settings(settings, clock)
    return DisabledExecution()


def _monitoring_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "monitoring" in overrides:
        return overrides["monitoring"]
    if getattr(settings.feature_flags, "pm6_post_trade", False):
        from botmoduleproject1.modules.pm6_post_trade.module import PM6PostTradeModule

        return PM6PostTradeModule.from_settings(settings, clock)
    return NullMonitoring()


def _ledger_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "ledger" in overrides:
        return overrides["ledger"]
    if getattr(settings.feature_flags, "pm7_persistence", False):
        from botmoduleproject1.modules.pm7_persistence.module import PM7PersistenceModule

        return PM7PersistenceModule.from_settings(settings, clock)
    return NullLedger()



def _storage_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "storage" in overrides:
        return overrides["storage"]
    if getattr(settings.feature_flags, "pm8_persistence", False):
        from botmoduleproject1.modules.pm8_persistence.module import PM8PersistenceModule

        return PM8PersistenceModule.from_settings(settings, clock)
    return NullStorage()


def _operator_module(settings: Settings, overrides: dict[str, Any], clock: ClockPort):
    if "operator" in overrides:
        return overrides["operator"]
    from botmoduleproject1.app.sequence_gate import OPERATOR_PLANE_FROZEN

    if OPERATOR_PLANE_FROZEN:
        return NullOperator()
    if getattr(settings.feature_flags, "pm8_operator", False):
        from botmoduleproject1.modules.pm8_operator.module import PM8OperatorModule

        return PM8OperatorModule.from_settings(settings, clock)
    return NullOperator()


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
        _market_data_module(settings, overrides, clock),
        _strategy_engine_module(settings, overrides, clock),
        _forecasting_module(settings, overrides, clock),
        _risk_module(settings, overrides, clock),
        _execution_module(settings, overrides, clock),
        _ledger_module(settings, overrides, clock),
        _storage_module(settings, overrides, clock),
        overrides.get("notifications") or NullNotifications(),
        _monitoring_module(settings, overrides, clock),
        _operator_module(settings, overrides, clock),
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

    try:
        op = registry.get("pm8_operator").instance
        storage = registry.get("pm8_persistence").instance
        bind = getattr(op, "bind_persistence", None)
        if bind is not None:
            bind(storage)
    except Exception:
        pass

    registry.validate_dependencies()
    return Container(
        settings=settings,
        clock=clock,
        registry=registry,
        health=health,
        lifecycle=lifecycle,
        extras=overrides,
    )
