"""Typed Protocols for PM4. Implementations live beside this file."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.pm2 import RankedCandidate
from botmoduleproject1.contracts.v1.risk import ExposureSnapshot, RiskPublicationBundle, RiskVerdict
from botmoduleproject1.contracts.v1.strategy import TradeIntent
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


@runtime_checkable
class PM4Module(Protocol):
    def metadata(self) -> ModuleMetadata: ...

    def is_ready(self) -> bool: ...

    def evaluate(self, intent: TradeIntent, exposure: ExposureSnapshot) -> RiskVerdict: ...

    def evaluate_request(self, request: RiskIntakeRequest) -> RiskPublicationBundle: ...

    def health_checks(self, kind: CheckKind) -> list[CheckResult]: ...


@runtime_checkable
class RiskIntakeGateway(Protocol):
    def normalize(
        self,
        intent: TradeIntent,
        exposure: ExposureSnapshot,
        *,
        candidate: RankedCandidate | None = None,
        forecast: ForecastOutput | None = None,
        as_of: datetime | None = None,
    ) -> RiskIntakeRequest: ...


@runtime_checkable
class HierarchicalRiskAllocator(Protocol):
    def allocate(self, request: RiskIntakeRequest, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class RiskAdmissionController(Protocol):
    def decide(self, request: RiskIntakeRequest, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class PositionSizer(Protocol):
    def size(self, request: RiskIntakeRequest, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class PortfolioHeatEngine(Protocol):
    def evaluate(self, *args, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class CorrelationEngine(Protocol):
    def evaluate(self, *args, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class DrawdownGovernor(Protocol):
    def evaluate(self, exposure: ExposureSnapshot): ...


@runtime_checkable
class PreTradeControlEngine(Protocol):
    def evaluate(self, *args, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class KillSwitchEngine(Protocol):
    def trip(self, **kwargs): ...  # noqa: ANN003

    def recover(self, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class GovernanceRegistry(Protocol):
    def snapshot(self) -> dict: ...


@runtime_checkable
class AuditRecorder(Protocol):
    def record(self, **kwargs): ...  # noqa: ANN003


@runtime_checkable
class HealthContributor(Protocol):
    def health_checks(self, kind: CheckKind) -> list[CheckResult]: ...


@runtime_checkable
class RiskPublicationGateway(Protocol):
    def publish(self, bundle: RiskPublicationBundle) -> RiskPublicationBundle: ...
