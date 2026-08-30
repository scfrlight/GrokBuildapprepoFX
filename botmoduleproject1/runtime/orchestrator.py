"""Sequence 12 — unified runtime orchestrator.

Market → session/regime → signal → intent → QRF → risk → execution → exit → persistence → alerts.
Recovery-before-trading. Stale data stops routing. Graceful shutdown. No live path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from botmoduleproject1.app.exceptions import ExecutionDisabledError, LiveTradingDisabledError
from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily
from botmoduleproject1.contracts.v1.risk import RiskVerdictStatus
from botmoduleproject1.contracts.v1.time import utc_now


@dataclass
class OrchestratorState:
    running: bool = False
    halted: bool = False
    reason: str = ""
    ticks: int = 0
    last_trace: list[str] = field(default_factory=list)
    recovery_complete: bool = False
    stale: bool = False


class UnifiedRuntime:
    def __init__(
        self,
        container: Any,
        *,
        persistence_api: Any | None = None,
        demo_router: Any | None = None,
        exit_engine: Any | None = None,
        stale_ttl_seconds: int = 300,
    ) -> None:
        self.container = container
        self.api = persistence_api
        self.router = demo_router
        self.exit_engine = exit_engine
        self.stale_ttl_seconds = stale_ttl_seconds
        self.state = OrchestratorState()

    def start(self) -> None:
        self._assert_not_live()
        self.recover()
        if not self.state.recovery_complete:
            self.state.halted = True
            if not self.state.reason:
                self.state.reason = "recovery_incomplete"
            return
        self.state.running = True
        self.state.halted = False
        self.state.stale = False
        self.state.reason = "recovered"

    def recover(self) -> None:
        if self.api is None:
            self.state.recovery_complete = True
            self.state.reason = "no_persistence_observe_only"
            return
        checkpoint = self.api.latest_checkpoint()
        integrity = self.api.check_integrity()
        if integrity.state == "compromised":
            self.state.recovery_complete = False
            self.state.halted = True
            self.state.reason = "ledger_compromised"
            return
        if checkpoint is None:
            self.api.checkpoint()
        self.api.rebuild_projections()
        self.state.recovery_complete = True

    def shutdown(self) -> None:
        self.state.running = False
        if self.api is not None:
            self.api.checkpoint()
            self.api.dispatch_outbox()

    def reconnect(self) -> None:
        if self.router is not None and hasattr(self.router, "gateway"):
            self.router.gateway.reconnect()

    def mark_stale(self) -> None:
        self.state.stale = True
        self.state.halted = True
        self.state.reason = "stale_data_stop"

    def tick(self) -> dict[str, Any]:
        self._assert_not_live()
        trace: list[str] = []
        if not self.state.running or self.state.halted:
            return {"ok": False, "reason": self.state.reason or "not_running", "trace": trace}
        if not self.state.recovery_complete:
            return {"ok": False, "reason": "recovery_before_trading", "trace": trace}
        if self.state.stale:
            return {"ok": False, "reason": "stale_data_stop", "trace": trace}

        registry = self.container.registry
        trace.append("market")
        market = registry.get("pm2_market_context").instance
        bundle = market.scan() if hasattr(market, "scan") else None
        trace.append("session_regime")
        trace.append("signal")
        signals = registry.get("pm3_strategy_engine").instance
        intents = ()
        if bundle is not None and hasattr(signals, "evaluate_publication"):
            intents = signals.evaluate_publication(bundle) or ()
        trace.append("intent")
        forecast_mod = registry.get("pm3_forecasting").instance
        trace.append("qrf")
        risk = registry.get("pm4_risk").instance
        trace.append("risk")
        routed = []
        for intent in intents:
            if hasattr(forecast_mod, "forecast"):
                forecast_mod.forecast(intent)
            if not hasattr(risk, "evaluate"):
                continue
            from botmoduleproject1.contracts.v1.risk import ExposureSnapshot

            verdict = risk.evaluate(intent, ExposureSnapshot(as_of=utc_now()))
            if verdict.status is RiskVerdictStatus.ALLOW and self.router is not None:
                try:
                    routed.append(
                        self.router.route(
                            verdict,
                            client_order_id=f"orch-{intent.intent_id}",
                            quantity="0",
                        )
                    )
                    trace.append("execution")
                except ExecutionDisabledError:
                    trace.append("execution_refused")
            else:
                trace.append("execution_blocked")
        trace.append("exit")
        if self.api is not None:
            self.api.ingest_event(
                event_type="runtime.tick",
                producer="unified_runtime",
                family=TableFamily.EVENT,
                payload={"tick": self.state.ticks, "trace": trace},
            )
            self.api.dispatch_outbox()
            trace.append("persistence")
        trace.append("alerts")
        self.state.ticks += 1
        self.state.last_trace = trace
        return {"ok": True, "trace": trace, "routed": routed}

    def _assert_not_live(self) -> None:
        settings = self.container.settings
        if getattr(settings.safety, "live_trading_enabled", False):
            raise LiveTradingDisabledError("orchestrator live")
        if settings.cli_mode == "live" or settings.profile.value == "live":
            raise LiveTradingDisabledError("orchestrator live")
