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
    NoTradeDecision,
    OhlcvBar,
    OrderRequest,
    PublicationBundle,
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

    def scan(self, as_of=None) -> PublicationBundle:
        from botmoduleproject1.contracts.v1.time import utc_now as _now

        when = as_of or _now()
        return PublicationBundle(
            as_of=when,
            diagnostics_summary={"enabled": False, "reason": "placeholder"},
            health_summary={"pm2": "disabled"},
        )

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
            description="Placeholder risk gate. Always DENY. Bound when enable_pm4_risk_gate is off.",
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
            "PM1 kernel refuses order submission. PM5 is closed unless "
            "enable_pm5_simulation is on (test/research). No MT5 send."
        )

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="execution.disabled",
                kind=kind,
                passed=True,
                critical=False,
                message="execution disabled in Sequence 07; DisabledExecution default bind",
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

    def evaluate_publication(self, bundle: PublicationBundle):
        return ()

    def evaluate_candidate(self, candidate) -> NoTradeDecision:
        as_of = getattr(candidate, "as_of", utc_now())
        symbol = getattr(candidate, "symbol", "UNKNOWN")
        return NoTradeDecision(
            symbol=symbol,
            reason="pm3_strategy_engine_placeholder",
            as_of=as_of,
            diagnostics={"enabled": False},
        )


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


class NullLedger:
    """Fail-closed PM7 bind. No durable journal until the flag is on."""

    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm7_ledger",
            version="0.0.0",
            capabilities=(Capability.LEDGER,),
            critical=False,
            description="Placeholder ledger. Bound when enable_pm7_persistence is off.",
        )

    def ingest(self, source) -> None:
        return None

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="ledger.placeholder",
                kind=kind,
                passed=True,
                critical=False,
                message="NullLedger; enable_pm7_persistence is off",
            )
        ]


class NullOperator:
    """Fail-closed PM8 bind. No commands until the flag is on."""

    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="pm8_operator",
            version="0.0.0",
            capabilities=(Capability.OPERATOR_CONTROL,),
            critical=False,
            description="Placeholder operator plane. Bound when enable_pm8_operator is off.",
        )

    def handle(self, command):
        from botmoduleproject1.contracts.v1.operator import CommandDisposition, CommandReceipt

        return CommandReceipt(
            correlation_id=getattr(command, "correlation_id"),
            causation_id=getattr(command, "event_id", None),
            idempotency_key=getattr(command, "idempotency_key", "null"),
            occurred_at=utc_now(),
            verb=getattr(command, "verb"),
            disposition=CommandDisposition.REFUSED,
            actor_id=getattr(getattr(command, "actor", None), "actor_id", "unknown"),
            role=getattr(getattr(command, "actor", None), "role", None) or __import__(
                "botmoduleproject1.contracts.v1.roles", fromlist=["OperatorRole"]
            ).OperatorRole.OBSERVER,
            message="NullOperator; enable_pm8_operator is off",
            reason_code="operator_disabled",
        )

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return [
            CheckResult(
                name="operator.placeholder",
                kind=kind,
                passed=True,
                critical=False,
                message="NullOperator; enable_pm8_operator is off",
            )
        ]

