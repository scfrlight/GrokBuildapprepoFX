"""Fail-closed placeholder providers. No broker, no orders, no strategy."""

from __future__ import annotations

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata
from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1 import (
    AlertEvent,
    ExecutionReport,
    ExposureSnapshot,
    ForecastOutput,
    JournalEntry,
    OhlcvBar,
    OrderRequest,
    RiskRejectionReason,
    RiskVerdict,
    RiskVerdictStatus,
    SignalEvent,
    Timeframe,
    TradeIntent,
)
from botmoduleproject1.contracts.v1.time import utc_now


class PlatformHealth:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm1_platform",
            version="0.1.0",
            capabilities=(Capability.PLATFORM, Capability.DIAGNOSTICS),
            critical=True,
            readiness_required=True,
            liveness_required=True,
        )

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="platform.kernel",
                kind=kind,
                passed=True,
                critical=True,
                message="composition root is assembled",
            )
        ]


class NullMarketData:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm2_market_context",
            version="0.0.0",
            capabilities=(Capability.MARKET_DATA,),
            critical=False,
            description="Placeholder. No broker connection.",
        )

    def latest_bar(self, symbol: str, timeframe: Timeframe) -> OhlcvBar | None:
        return None

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="market_data.placeholder",
                kind=kind,
                passed=True,
                critical=False,
                message="placeholder; no feed attached",
            )
        ]


class NullRiskGate:
    """Fail closed: never ALLOW."""

    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm4_risk",
            version="0.0.0",
            capabilities=(Capability.RISK_GATING,),
            critical=True,
            readiness_required=True,
            description="Placeholder risk gate. Always DENY.",
        )

    def is_ready(self) -> bool:
        return False

    def evaluate(self, intent: TradeIntent, exposure: ExposureSnapshot) -> RiskVerdict:
        return RiskVerdict(
            intent_id=intent.intent_id,
            correlation_id=intent.correlation_id,
            causation_id=intent.event_id,
            occurred_at=utc_now(),
            status=RiskVerdictStatus.DENY,
            reasons=(RiskRejectionReason.ENGINE_UNAVAILABLE,),
            detail="PM4 is a placeholder. Fail closed.",
        )

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        ready = self.is_ready()
        return [
            CheckResult(
                name="risk_gate.ready",
                kind=kind,
                passed=kind is not CheckKind.READINESS or ready,
                critical=kind is CheckKind.READINESS,
                message="placeholder risk engine is not ready for orders",
            )
        ]


class DisabledExecution:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm5_execution",
            version="0.0.0",
            capabilities=(Capability.EXECUTION,),
            critical=False,
            description="Orders are refused at the kernel.",
        )

    def submit(self, request: OrderRequest) -> ExecutionReport:
        raise ExecutionDisabledError(
            "PM1 kernel refuses order submission. PM5 is not implemented."
        )

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="execution.disabled",
                kind=kind,
                passed=True,
                critical=False,
                message="execution disabled in Sequence 01",
            )
        ]


class NullStorage:
    def __init__(self) -> None:
        self.entries: list[JournalEntry] = []

    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm8_persistence",
            version="0.0.0",
            capabilities=(Capability.STORAGE,),
            critical=False,
        )

    def append(self, entry: JournalEntry) -> None:
        self.entries.append(entry)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="storage.placeholder",
                kind=kind,
                passed=True,
                critical=False,
                message="in-memory no-op",
            )
        ]


class NullNotifications:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="notifications",
            version="0.0.0",
            capabilities=(Capability.NOTIFICATIONS,),
            critical=False,
        )

    def publish(self, alert: AlertEvent) -> None:
        return None


class NullModel:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm3_forecasting",
            version="0.0.0",
            capabilities=(Capability.FORECASTING,),
            critical=False,
            description="PM3 forecasting placeholder. Not the Strategy Engine.",
        )

    def forecast(self, intent: TradeIntent) -> ForecastOutput | None:
        return None


class NullSignals:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm3_strategy_engine",
            version="0.0.0",
            capabilities=(Capability.SIGNALS,),
            critical=False,
            description="PM3-Strategy Engine placeholder. Produces no intents.",
        )

    def latest_signal(self, symbol: str) -> SignalEvent | None:
        return None


class NullMonitoring:
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm6_monitoring",
            version="0.0.0",
            capabilities=(Capability.TELEMETRY,),
            critical=False,
        )

    def observe(self, entry: JournalEntry) -> None:
        return None
