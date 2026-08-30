"""PM4 Risk Gate orchestrator. Deny-by-default. Never an order. Never PM5."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.pm2 import RankedCandidate
from botmoduleproject1.contracts.v1.risk import (
    ConcentrationState,
    DrawdownStage,
    ExposureSnapshot,
    HandoffEligibility,
    KillSwitchScope,
    KillSwitchStatus,
    PositionSizingDecision,
    RiskAdmissionDecision,
    RiskEventType,
    RiskMode,
    RiskPublicationBundle,
    RiskRejectionReason,
    RiskSeverity,
    RiskVerdict,
    RiskVerdictStatus,
)
from botmoduleproject1.contracts.v1.strategy import TradeIntent
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.contracts.v1.pm4_capital import CapitalEvaluationResult, RiskEvaluationRequest
from botmoduleproject1.modules.pm4_risk_gate.budgeting.hierarchical_allocator import HierarchicalRiskAllocator
from botmoduleproject1.modules.pm4_risk_gate.capabilities import PM4_RISK_GATE_METADATA
from botmoduleproject1.modules.pm4_risk_gate.capital.evaluation import CapitalEvaluationService
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig, config_from_settings
from botmoduleproject1.modules.pm4_risk_gate.concentration.correlation_engine import CorrelationEngine
from botmoduleproject1.modules.pm4_risk_gate.controls.pretrade_controls import PreTradeControlEngine
from botmoduleproject1.modules.pm4_risk_gate.domain.ids import new_id
from botmoduleproject1.modules.pm4_risk_gate.domain.policies import MODE_BLOCKS_NEW_RISK, PRODUCER
from botmoduleproject1.modules.pm4_risk_gate.drawdown.drawdown_governor import DrawdownGovernor
from botmoduleproject1.modules.pm4_risk_gate.governance.audit import AuditRecorder
from botmoduleproject1.modules.pm4_risk_gate.health import health_checks as pm4_health
from botmoduleproject1.modules.pm4_risk_gate.health.degraded_modes import mode_from
from botmoduleproject1.modules.pm4_risk_gate.heat.heat_engine import PortfolioHeatEngine
from botmoduleproject1.modules.pm4_risk_gate.infrastructure.repositories.in_memory_incidents import (
    InMemoryIncidentRepository,
)
from botmoduleproject1.modules.pm4_risk_gate.infrastructure.repositories.in_memory_inventory import (
    InMemoryInventoryRepository,
)
from botmoduleproject1.modules.pm4_risk_gate.infrastructure.repositories.in_memory_state import InMemoryRiskState
from botmoduleproject1.modules.pm4_risk_gate.intake.admission import RiskAdmissionController
from botmoduleproject1.modules.pm4_risk_gate.intake.risk_gateway import RiskIntakeGateway
from botmoduleproject1.modules.pm4_risk_gate.intake.validators import _stop_distance, validate_intake
from botmoduleproject1.modules.pm4_risk_gate.kill.kill_switch_engine import KillSwitchEngine
from botmoduleproject1.modules.pm4_risk_gate.manifest import module_manifest
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest
from botmoduleproject1.modules.pm4_risk_gate.publication.handoff_gateway import handoff_eligibility
from botmoduleproject1.modules.pm4_risk_gate.publication.publisher import RiskPublisher
from botmoduleproject1.modules.pm4_risk_gate.sizing.position_sizer import PositionSizer

_ZERO = Decimal("0")


def _empty_sizing(equity: Decimal) -> PositionSizingDecision:
    return PositionSizingDecision(
        recommended_size=_ZERO,
        base_risk_percentage=_ZERO,
        adjusted_risk_percentage=_ZERO,
        stop_distance=_ZERO,
        stop_distance_basis="none",
        uncertainty_discount=_ZERO,
        predictive_quality_factor=_ZERO,
        drawdown_throttle=_ZERO,
        liquidity_factor=_ZERO,
        correlation_penalty=_ZERO,
        heat_cap_factor=_ZERO,
        hard_cap_applied=False,
        final_size_rationale="denied before or after sizing; size is zero",
        account_equity=equity,
        risk_amount=_ZERO,
    )


class PM4RiskGateModule:
    """Registered as pm4_risk. Implements RiskGate. Never constructs orders."""

    def __init__(
        self,
        config: Pm4RiskGateConfig,
        clock: Any,
        *,
        feature_enabled: bool = True,
        persistence_api: Any | None = None,
    ) -> None:
        self.config = config
        self.clock = clock
        self.feature_enabled = feature_enabled
        self.persistence_api = persistence_api
        self.gateway = RiskIntakeGateway()
        self.admission = RiskAdmissionController(config)
        self.allocator = HierarchicalRiskAllocator(config)
        self.sizer = PositionSizer(config)
        self.heat_engine = PortfolioHeatEngine(config)
        self.correlation = CorrelationEngine(config)
        self.drawdown = DrawdownGovernor(config)
        self.pretrade = PreTradeControlEngine(config)
        self.kill = KillSwitchEngine(config)
        self.inventory = InMemoryInventoryRepository()
        self.incidents = InMemoryIncidentRepository()
        self.state = InMemoryRiskState()
        self.audit = AuditRecorder()
        self.publisher = RiskPublisher()
        self._forced_mode: RiskMode | None = None
        self._last_mode: RiskMode = RiskMode.NORMAL
        self.capital = CapitalEvaluationService(
            config,
            clock=clock,
            persistence=persistence_api,
            require_persistence=persistence_api is not None,
        )

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM4RiskGateModule:
        flag = bool(getattr(settings, "feature_flags").risk_engine)
        return cls(config_from_settings(settings), clock, feature_enabled=flag)

    def metadata(self) -> ModuleMetadata:
        return PM4_RISK_GATE_METADATA

    def manifest(self) -> dict:
        return module_manifest()

    def is_ready(self) -> bool:
        return bool(self.feature_enabled)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        latched = self.kill.state.status in {KillSwitchStatus.TRIPPED, KillSwitchStatus.LATCHED}
        return pm4_health(
            kind,
            feature_enabled=self.feature_enabled,
            ready=self.is_ready(),
            kill_latched=latched,
        )

    def trip_kill_switch(
        self,
        reason: str,
        *,
        scope: KillSwitchScope = KillSwitchScope.ACCOUNT,
        scope_id: str | None = None,
        actor: str = "operator",
    ):
        now = self.clock.now()
        state = self.kill.trip(reason=reason, now=now, scope=scope, scope_id=scope_id, actor=actor)
        self.audit.record(
            occurred_at=now,
            kind=RiskEventType.KILL_SWITCH,
            summary=f"kill-switch latched: {reason}",
            correlation_id=new_id(),
            attributes={"actor": actor, "scope": scope.value},
        )
        self.incidents.raise_incident(
            now=now, title="kill_switch", severity=RiskSeverity.CRITICAL, detail=reason
        )
        return state

    def recover_kill_switch(self, reason: str, *, actor: str = "operator"):
        now = self.clock.now()
        state = self.kill.recover(reason=reason, actor=actor, now=now)
        self.audit.record(
            occurred_at=now,
            kind=RiskEventType.RECOVERY,
            summary=f"kill-switch recovery attempted: {reason}",
            correlation_id=new_id(),
            attributes={"actor": actor, "status": state.status.value},
        )
        return state

    def force_mode(self, mode: RiskMode | None) -> None:
        self._forced_mode = mode

    def evaluate(self, intent: TradeIntent, exposure: ExposureSnapshot) -> RiskVerdict:
        """RiskGate protocol. Missing PM2/PM3 artifacts deny-by-default."""
        bundle = self.evaluate_intent(intent, exposure)
        return bundle.verdict

    def evaluate_capital(self, request: RiskEvaluationRequest) -> CapitalEvaluationResult:
        """Capital-management pipeline. Never an order. execution_allowed stays false."""
        return self.capital.evaluate(request)

    def evaluate_intent(
        self,
        intent: TradeIntent,
        exposure: ExposureSnapshot,
        *,
        candidate: RankedCandidate | None = None,
        forecast: ForecastOutput | None = None,
        as_of: datetime | None = None,
        mid_price: Decimal | None = None,
        spread: Decimal | None = None,
        session: str | None = None,
    ) -> RiskPublicationBundle:
        request = self.gateway.normalize(
            intent,
            exposure,
            candidate=candidate,
            forecast=forecast,
            as_of=as_of,
            mid_price=mid_price,
            spread=spread,
            session=session,
        )
        return self.evaluate_request(request)

    def evaluate_request(self, request: RiskIntakeRequest) -> RiskPublicationBundle:
        now = ensure_aware_utc(self.clock.now(), "now")
        key = request.intent.idempotency_key
        cached = self.state.get(key)
        if cached is not None:
            return cached

        equity = request.exposure.equity if request.exposure.equity > 0 else self.config.account_equity
        dd_card = self.drawdown.evaluate(request.exposure)
        if dd_card.throttle_stage is DrawdownStage.KILL_PROTECTED:
            self.kill.trip(reason="drawdown_kill_protected", now=now, actor="automatic")

        intake_reasons = list(validate_intake(request, self.config, now))
        if not self.feature_enabled:
            intake_reasons.insert(0, RiskRejectionReason.FEATURE_DISABLED)

        sleeve = request.intent.profile_id
        cluster = request.candidate.correlation_cluster if request.candidate else None
        kill_blocks = self.kill.blocks(request.intent.symbol, sleeve, cluster)
        if kill_blocks:
            intake_reasons.append(RiskRejectionReason.KILL_SWITCH)

        mode = mode_from(
            drawdown=dd_card.throttle_stage,
            kill_blocks=kill_blocks,
            forced=self._forced_mode,
        )
        self._last_mode = mode

        stop = _stop_distance(request) or _ZERO
        naive_risk = equity * self.config.max_per_trade_risk_pct
        concentration = self.correlation.evaluate(request, request.exposure, naive_risk, equity)
        heat = self.heat_engine.evaluate(
            request.exposure,
            concentration,
            naive_risk,
            equity,
            stressed=concentration.stressed_concentration_state
            in {ConcentrationState.STRESSED, ConcentrationState.CROWDED, ConcentrationState.BLOCKED},
        )
        budget = self.allocator.allocate(
            request, equity=equity, proposed_risk=naive_risk, drawdown=dd_card
        )
        admission = self.admission.decide(
            request,
            intake_reasons=intake_reasons,
            drawdown=dd_card,
            heat=heat,
            concentration=concentration,
            kill=self.kill.state,
            mode=mode,
            budget_headroom=budget.residual_headroom,
            feature_enabled=self.feature_enabled,
            session=request.session,
        )

        sizing = _empty_sizing(equity)
        pretrade_duplicate = False
        if admission.decision in {RiskAdmissionDecision.APPROVE, RiskAdmissionDecision.REDUCE}:
            sizing = self.sizer.size(
                request,
                equity=equity,
                drawdown=dd_card,
                concentration=concentration,
                heat=heat,
                budget_headroom=budget.residual_headroom,
            )
            proposed = sizing.risk_amount
            heat = self.heat_engine.evaluate(
                request.exposure,
                concentration,
                proposed,
                equity,
                stressed=heat.heat_regime.value in {"hot", "critical", "stressed"},
            )
            budget = self.allocator.allocate(
                request, equity=equity, proposed_risk=proposed, drawdown=dd_card
            )
            if sizing.recommended_size <= 0:
                admission = admission.model_copy(
                    update={
                        "decision": RiskAdmissionDecision.REJECT,
                        "reasons": admission.reasons + ("size_zero",),
                        "vetoes": admission.vetoes + (RiskRejectionReason.SIZE_ZERO.value,),
                        "detail": "sized to zero after discounts",
                    }
                )
                sizing = _empty_sizing(equity)

        pretrade = self.pretrade.evaluate(
            request,
            sizing if sizing.recommended_size > 0 else _empty_sizing(equity),
            now,
            duplicate=pretrade_duplicate,
            route_open=False,
        )
        if admission.decision in {RiskAdmissionDecision.APPROVE, RiskAdmissionDecision.REDUCE}:
            if not pretrade.passed:
                admission = admission.model_copy(
                    update={
                        "decision": RiskAdmissionDecision.REJECT,
                        "reasons": admission.reasons + tuple(b.value for b in pretrade.breach_reasons),
                        "detail": "pre-trade controls rejected",
                    }
                )
                sizing = _empty_sizing(equity)

        status, reasons, detail = self._verdict_from(admission, mode)
        eligibility = handoff_eligibility(
            admission=admission.decision,
            verdict=status,
            kill=self.kill.state.status,
            mode=mode,
            pretrade=pretrade,
        )
        if status is RiskVerdictStatus.ALLOW:
            eligibility = HandoffEligibility.ELIGIBLE_PENDING_PM5
        expires = now + timedelta(seconds=self.config.verdict_ttl_seconds)
        verdict = RiskVerdict(
            intent_id=request.intent.intent_id,
            event_id=new_id(),
            correlation_id=request.intent.correlation_id,
            causation_id=request.intent.event_id,
            idempotency_key=key,
            occurred_at=now,
            status=status,
            reasons=reasons,
            detail=detail,
            expires_at=expires,
            producer=PRODUCER,
            recommended_volume=sizing.recommended_size if status is RiskVerdictStatus.ALLOW else None,
            handoff_eligibility=eligibility,
        )
        bundle = RiskPublicationBundle(
            event_id=verdict.event_id,
            correlation_id=verdict.correlation_id,
            causation_id=verdict.causation_id,
            idempotency_key=key,
            occurred_at=now,
            intent_id=request.intent.intent_id,
            candidate_id=request.candidate.candidate_id if request.candidate else None,
            forecast_id=request.forecast.forecast_id if request.forecast else None,
            symbol=request.intent.symbol,
            verdict=verdict,
            admission=admission,
            budget=budget,
            sizing=sizing,
            heat=heat,
            concentration=concentration,
            drawdown=dd_card,
            pretrade=pretrade,
            kill_switch=self.kill.state,
            diagnostics_summary={
                "risk_mode": mode.value,
                "feature_enabled": self.feature_enabled,
                "stop_distance": str(stop),
                "execution_permitted": False,
                "pm5": "closed",
                "durable": False,
            },
            audit_summary=self.audit.summary(),
            handoff_eligibility=eligibility,
            execution_permitted=False,
            risk_mode=mode,
        )
        if status is RiskVerdictStatus.ALLOW:
            self.allocator.consume("account", sizing.risk_amount)
            sleeve_key = request.intent.profile_id or "default_sleeve"
            self.allocator.consume(f"sleeve:{sleeve_key}", sizing.risk_amount)
            self.allocator.consume(f"symbol:{request.intent.symbol}", sizing.risk_amount)
        self.publisher.publish(bundle)
        self.state.put(key, bundle)
        self.audit.record(
            occurred_at=now,
            kind=RiskEventType.PUBLICATION,
            summary=f"risk {status.value} {request.intent.symbol}",
            correlation_id=verdict.correlation_id,
            causation_id=verdict.causation_id,
            idempotency_key=key,
            attributes={
                "admission": admission.decision.value,
                "handoff": eligibility.value,
                "size": str(sizing.recommended_size),
            },
        )
        if status is not RiskVerdictStatus.ALLOW:
            self.incidents.raise_incident(
                now=now,
                title="risk_deny",
                severity=RiskSeverity.MEDIUM,
                detail=detail,
            )
        return bundle

    def _verdict_from(
        self, admission, mode: RiskMode
    ) -> tuple[RiskVerdictStatus, tuple[RiskRejectionReason, ...], str]:
        mapped: list[RiskRejectionReason] = []
        for raw in admission.vetoes + admission.reasons:
            try:
                mapped.append(RiskRejectionReason(raw))
            except ValueError:
                mapped.append(RiskRejectionReason.POLICY)
        if admission.decision is RiskAdmissionDecision.KILL_PROTECTED:
            return (
                RiskVerdictStatus.HALT,
                tuple(dict.fromkeys(mapped or (RiskRejectionReason.KILL_SWITCH,))),
                "kill-switch latched; no new risk",
            )
        if admission.decision is RiskAdmissionDecision.FREEZE:
            return (
                RiskVerdictStatus.DENY,
                tuple(dict.fromkeys(mapped or (RiskRejectionReason.DRAWDOWN_LIMIT,))),
                "drawdown freeze; no new risk",
            )
        if admission.decision is RiskAdmissionDecision.REJECT:
            return (
                RiskVerdictStatus.DENY,
                tuple(dict.fromkeys(mapped or (RiskRejectionReason.POLICY,))),
                admission.detail or "rejected",
            )
        if mode in MODE_BLOCKS_NEW_RISK:
            return (
                RiskVerdictStatus.DENY,
                (RiskRejectionReason.DEGRADED_MODE,),
                f"degraded mode {mode.value}",
            )
        if admission.decision in {RiskAdmissionDecision.APPROVE, RiskAdmissionDecision.REDUCE}:
            return (
                RiskVerdictStatus.ALLOW,
                (),
                "risk-governed handoff pending PM5; not an order",
            )
        return (RiskVerdictStatus.DENY, (RiskRejectionReason.UNKNOWN_STATE,), "unknown admission")
