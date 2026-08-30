"""Sequence 14 observability module. Always bound. Never a trading path."""

from __future__ import annotations

import sys
from typing import Any

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.settings import Settings
from botmoduleproject1.contracts.v1.observability import (
    ErrorCode,
    HealthReport,
    LogLevel,
    ObservabilitySnapshot,
    ReadinessReport,
    StructuredLogEvent,
)
from botmoduleproject1.modules.observability.errors import ERROR_CATALOG
from botmoduleproject1.modules.observability.health_model import evaluate
from botmoduleproject1.modules.observability.logging_events import emit_event
from botmoduleproject1.modules.observability.metrics import METRIC_CATALOG, MetricRegistry
from botmoduleproject1.modules.observability.runbooks import RUNBOOKS


OBSERVABILITY_METADATA = ModuleMetadata(
    name="observability",
    version="0.14.0",
    capabilities=(Capability.TELEMETRY, Capability.DIAGNOSTICS),
    critical=False,
    description="Sequence 14 observability / operations. Observe-only.",
)


class ObservabilityModule:
    def __init__(self, *, settings: Settings | None = None, clock: Any = None) -> None:
        self.settings = settings
        self.clock = clock
        self.metrics = MetricRegistry()
        self.events: list[StructuredLogEvent] = []

    @classmethod
    def from_settings(cls, settings: Settings, clock: Any) -> ObservabilityModule:
        return cls(settings=settings, clock=clock)

    def metadata(self) -> ModuleMetadata:
        return OBSERVABILITY_METADATA

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        if kind is CheckKind.LIVENESS:
            return [
                CheckResult(
                    name="observability.liveness",
                    kind=kind,
                    passed=True,
                    critical=True,
                    message="process assembled",
                )
            ]
        if kind is CheckKind.READINESS:
            return [
                CheckResult(
                    name="observability.trading_readiness_closed",
                    kind=kind,
                    passed=True,
                    critical=True,
                    message="trading_readiness remains false",
                )
            ]
        return [
            CheckResult(
                name="observability.startup",
                kind=kind,
                passed=True,
                critical=False,
                message="observe-only module bound",
            )
        ]

    def log(
        self,
        event_name: str,
        *,
        status: str = "ok",
        level: LogLevel = LogLevel.INFO,
        error_code: ErrorCode | None = None,
        metadata: dict[str, Any] | None = None,
        **fields: Any,
    ) -> StructuredLogEvent:
        profile = self.settings.profile.value if self.settings is not None else "test"
        event = emit_event(
            event_name=event_name,
            module="observability",
            sequence=14,
            profile=profile,
            status=status,
            level=level,
            error_code=error_code,
            metadata=metadata,
            **fields,
        )
        self.events.append(event)
        return event

    def reports(
        self,
        settings: Settings | None = None,
        *,
        lifecycle: LifecycleState = LifecycleState.DEGRADED,
        persistence_ok: bool = True,
        persistence_enabled: bool = False,
        integrity_ok: bool = True,
        stale_data: bool = False,
        telegram_bound: bool = False,
        operator_bound: bool = False,
    ) -> tuple[HealthReport, ReadinessReport]:
        cfg = settings or self.settings
        if cfg is None:
            raise RuntimeError("settings required")
        return evaluate(
            cfg,
            lifecycle=lifecycle,
            persistence_ok=persistence_ok,
            persistence_enabled=persistence_enabled,
            integrity_ok=integrity_ok,
            stale_data=stale_data,
            telegram_bound=telegram_bound,
            operator_bound=operator_bound,
        )

    def snapshot(
        self,
        settings: Settings | None = None,
        *,
        lifecycle: LifecycleState = LifecycleState.DEGRADED,
        persistence_enabled: bool = False,
        telegram_bound: bool = False,
        stale_data: bool = False,
        integrity_ok: bool = True,
    ) -> ObservabilitySnapshot:
        cfg = settings or self.settings
        if cfg is None:
            raise RuntimeError("settings required")
        health, readiness = self.reports(
            cfg,
            lifecycle=lifecycle,
            persistence_enabled=persistence_enabled,
            telegram_bound=telegram_bound,
            stale_data=stale_data,
            integrity_ok=integrity_ok,
        )
        self.metrics.set("botmodule.health.transitions", 1.0, module="observability", dimension="liveness", outcome="pass")
        return ObservabilitySnapshot(
            health=health,
            readiness=readiness,
            metrics=self.metrics.snapshot(),
            metric_catalog_count=len(METRIC_CATALOG),
            runbook_count=len(RUNBOOKS),
            error_catalog_count=len(ERROR_CATALOG),
            flags=cfg.feature_flags.enabled_map(),
            live_trading_enabled=bool(cfg.safety.live_trading_enabled),
            telegram_bound=telegram_bound,
            python="{}.{}.{}".format(*sys.version_info[:3]),
        )
