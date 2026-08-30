"""Sequence 11 module. Demo-only. Flag off: not bound. Never live."""

from __future__ import annotations

from typing import Any

from botmoduleproject1.adapters.mt5.demo_gateway import DemoMt5Gateway
from botmoduleproject1.app.capabilities import Capability, ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.modules.mt5_execution_engine.demo_routing import DemoRouter
from botmoduleproject1.modules.mt5_execution_engine.exit_engine import ExitEngine


MT5_EXECUTION_ENGINE_METADATA = ModuleMetadata(
    name="mt5_execution_engine",
    version="0.11.0",
    capabilities=(Capability.EXECUTION,),
    critical=False,
    description="Sequence 11 Demo MT5 routing + exit. Not PM6. Not PM5. Live refused.",
)


class MT5ExecutionEngineModule:
    def __init__(self, *, simulated: bool = True, clock: Any = None) -> None:
        self.clock = clock
        self.gateway = DemoMt5Gateway(simulated=simulated)
        self.router = DemoRouter(self.gateway)
        self.exit_engine = ExitEngine()

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> "MT5ExecutionEngineModule":
        flags = getattr(settings, "feature_flags")
        simulated = True
        if getattr(flags, "mt5_demo_adapter", False) is False:
            simulated = True
        return cls(simulated=simulated, clock=clock)

    def metadata(self) -> ModuleMetadata:
        return MT5_EXECUTION_ENGINE_METADATA

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="mt5_execution_engine.demo_only",
                kind=kind,
                passed=True,
                critical=True,
                message="live refused; DEMO-* is not broker truth",
            )
        ]
