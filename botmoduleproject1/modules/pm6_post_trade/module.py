"""PM6 post-trade orchestrator. Observe-only. Never an order. Never broker truth."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.execution import ExecutionPublicationBundle
from botmoduleproject1.contracts.v1.journal import JournalEntry
from botmoduleproject1.contracts.v1.post_trade import (
    ControlRequest,
    ControlRequestKind,
    IncidentRecord,
    IncidentState,
    IncidentType,
    IntakeDisposition,
    MonitoringState,
    OperationalTruthBundle,
    OrderlyWithdrawalPlan,
    PostTradeAlert,
    SeverityLevel,
    TruthSource,
    WithdrawalState,
)
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.modules.pm6_post_trade.capabilities import PM6_POST_TRADE_METADATA
from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig, config_from_settings
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id
from botmoduleproject1.modules.pm6_post_trade.domain.states import worse
from botmoduleproject1.modules.pm6_post_trade.escalation.router import escalate
from botmoduleproject1.modules.pm6_post_trade.evidence.registry import EvidenceRegistry
from botmoduleproject1.modules.pm6_post_trade.governance.intelligence import governance_packet, validation_packet
from botmoduleproject1.modules.pm6_post_trade.health import health_checks as pm6_health
from botmoduleproject1.modules.pm6_post_trade.incidents.lifecycle import transit as incident_transit
from botmoduleproject1.modules.pm6_post_trade.incidents.orchestrator import IncidentOrchestrator
from botmoduleproject1.modules.pm6_post_trade.infrastructure.repositories import (
    InMemoryAlertRepository,
    InMemoryEvidenceRepository,
    InMemoryGovernanceRepository,
    InMemoryIncidentRepository,
    InMemoryMonitoringRepository,
)
from botmoduleproject1.modules.pm6_post_trade.intake.gateway import PostTradeIntakeGateway
from botmoduleproject1.modules.pm6_post_trade.manifest import module_manifest
from botmoduleproject1.modules.pm6_post_trade.monitoring.lane_manager import build_lanes
from botmoduleproject1.modules.pm6_post_trade.monitoring.post_trade_control import evaluate_controls
from botmoduleproject1.modules.pm6_post_trade.monitoring.real_time import snapshot as build_snapshot
from botmoduleproject1.modules.pm6_post_trade.publication.publisher import PublicationGateway
from botmoduleproject1.modules.pm6_post_trade.remediation.action_router import TYPE_TO_REQUEST
from botmoduleproject1.modules.pm6_post_trade.remediation.tasks import close_task, open_task
from botmoduleproject1.modules.pm6_post_trade.surveillance.engine import SurveillanceEngine
from botmoduleproject1.modules.pm6_post_trade.withdrawal.planner import WithdrawalPlanner


class PM6PostTradeModule:
    """Registered as pm6_monitoring when enable_pm6_post_trade is on."""

    def __init__(
        self,
        config: Pm6PostTradeConfig,
        clock: Any,
        *,
        feature_enabled: bool = True,
        surveillance_enabled: bool = True,
        incident_enabled: bool = True,
        governance_enabled: bool = True,
        withdrawal_enabled: bool = True,
    ) -> None:
        self.config = config
        self.clock = clock
        self.feature_enabled = feature_enabled
        self.surveillance_enabled = surveillance_enabled and feature_enabled
        self.incident_enabled = incident_enabled and feature_enabled
        self.governance_enabled = governance_enabled and feature_enabled
        self.withdrawal_enabled = withdrawal_enabled and feature_enabled
        self.gateway = PostTradeIntakeGateway()
        self.surv = SurveillanceEngine(config)
        self.incidents = IncidentOrchestrator()
        self.withdrawal = WithdrawalPlanner()
        self.evidence = EvidenceRegistry()
        self.publisher = PublicationGateway()
        self.monitoring_repo = InMemoryMonitoringRepository()
        self.alert_repo = InMemoryAlertRepository()
        self.incident_repo = InMemoryIncidentRepository()
        self.evidence_repo = InMemoryEvidenceRepository()
        self.governance_repo = InMemoryGovernanceRepository()
        self.escalations = []
        self.tasks = []
        self.control_requests: list[ControlRequest] = []
        self.last_truth = TruthSource.UNKNOWN
        self._last_bundle: OperationalTruthBundle | None = None

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM6PostTradeModule:
        flags = getattr(settings, "feature_flags")
        cfg = config_from_settings(settings)
        return cls(
            cfg,
            clock,
            feature_enabled=bool(getattr(flags, "pm6_post_trade", False)),
            surveillance_enabled=bool(getattr(flags, "pm6_surveillance", True)),
            incident_enabled=bool(getattr(flags, "pm6_incident_response", True)),
            governance_enabled=bool(getattr(flags, "pm6_governance", True)),
            withdrawal_enabled=bool(getattr(flags, "pm6_withdrawal", True)),
        )

    def metadata(self) -> ModuleMetadata:
        return PM6_POST_TRADE_METADATA

    def manifest(self) -> dict:
        return module_manifest()

    def is_ready(self) -> bool:
        return bool(self.feature_enabled)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return pm6_health(
            kind,
            enabled=self.feature_enabled,
            ready=self.is_ready(),
            truth=self.last_truth.value,
        )

    def observe(
        self,
        execution: ExecutionPublicationBundle | JournalEntry | None = None,
        risk: RiskPublicationBundle | None = None,
        *,
        operator_action: dict | None = None,
    ) -> OperationalTruthBundle:
        now = self.clock.now()
        if isinstance(execution, JournalEntry):
            self.evidence.note(f"{now.isoformat()} journal {execution.summary}")
            execution = None
        intake = self.gateway.validate(
            execution,
            risk,
            now=now,
            config=self.config,
            feature_enabled=self.feature_enabled,
        )
        obs = self.gateway.normalize(execution, risk, now)
        self.last_truth = obs.truth
        if execution is not None:
            self.surv.last_event = execution.occurred_at
        elif risk is not None:
            self.surv.last_event = risk.occurred_at

        self.evidence.note(f"{now.isoformat()} observe {intake.disposition.value}")
        findings = []
        if intake.disposition is not IntakeDisposition.REJECTED or "sim_labelled_broker_truth" in intake.reasons:
            withdrawal_active = bool(
                self.withdrawal.plan
                and self.withdrawal.plan.state
                not in {WithdrawalState.NOT_REQUIRED, WithdrawalState.COMPLETED}
            )
            findings.extend(evaluate_controls(obs, withdrawal_active=withdrawal_active))
            if self.surveillance_enabled:
                findings.extend(self.surv.extra_findings(obs, now))

        alerts: list[PostTradeAlert] = []
        order_id = execution.order.order_id if execution is not None and execution.order is not None else None
        for finding in findings:
            if not self.surveillance_enabled and finding.detector in {"submit_burst", "reject_burst", "fill_burst"}:
                continue
            alert = self.surv.to_alert(finding, now=now, truth=obs.truth, order_id=order_id)
            alerts.append(alert)
            self.alert_repo.add(alert)
            self.surv.alerts.append(alert)
            self.evidence.note(f"{now.isoformat()} alert {finding.detector} suppressed={alert.suppressed}")
            if (
                self.incident_enabled
                and finding.incident_type is not None
                and finding.severity in {SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL}
                and not alert.suppressed
            ):
                inc = self.incidents.open_from(finding, alert, now=now, truth=obs.truth)
                self.incident_repo.add(inc)
                if inc.state is IncidentState.ESCALATED:
                    esc = escalate(inc, now=now, config=self.config)
                    self.escalations.append(esc)
                    task = open_task(inc, now=now)
                    self.tasks.append(task)
                    kind = TYPE_TO_REQUEST.get(inc.incident_type)
                    if kind is not None:
                        self.control_requests.append(
                            ControlRequest(
                                request_id=new_id(),
                                occurred_at=now,
                                kind=kind,
                                scope=inc.affected_scope,
                                reason=inc.detail,
                                actor="pm6",
                                approval_required=True,
                                broker_command=False,
                            )
                        )
                if self.withdrawal_enabled and inc.incident_type in {
                    IncidentType.KILL_STATE_BREACH,
                    IncidentType.UNEXPECTED_TRADING_CONTINUATION,
                    IncidentType.ORDERLY_WITHDRAWAL_REQUIRED,
                }:
                    if self.withdrawal.plan is None or self.withdrawal.plan.state in {
                        WithdrawalState.NOT_REQUIRED,
                        WithdrawalState.COMPLETED,
                        WithdrawalState.FAILED,
                    }:
                        self.withdrawal.recommend(inc, now=now, scope=inc.affected_scope)

        state = MonitoringState.HEALTHY
        recon = "unavailable"
        mode = "disabled"
        if execution is not None:
            mode = execution.execution_mode.value
            if execution.reconciliation is not None:
                recon = execution.reconciliation.outcome.value
        if recon in {"degraded", "unavailable"}:
            state = worse(state, MonitoringState.DEGRADED)
        if intake.disposition is IntakeDisposition.QUARANTINED:
            state = worse(state, MonitoringState.WARNING)
        if any(a.severity is SeverityLevel.HIGH and not a.suppressed for a in alerts):
            state = worse(state, MonitoringState.WARNING)
        if self.incidents.open():
            state = worse(state, MonitoringState.INCIDENT_ACTIVE)
        if any(a.severity is SeverityLevel.CRITICAL and not a.suppressed for a in alerts):
            state = worse(state, MonitoringState.CRITICAL)
        if self.withdrawal.plan and self.withdrawal.plan.state in {
            WithdrawalState.INITIATED,
            WithdrawalState.IN_PROGRESS,
            WithdrawalState.CONFIRMED,
        }:
            state = worse(state, MonitoringState.WITHDRAWAL_IN_PROGRESS)

        controls = []
        if obs.kill:
            controls.append("kill_latched")
        if obs.freeze:
            controls.append("freeze")
        if execution is not None:
            controls.append(execution.operating_state.value)

        fills = len(execution.fills) if execution is not None else 0
        open_orders = 1 if execution is not None and execution.order is not None and execution.receipt.accepted else 0
        positions = 1 if execution is not None and execution.order is not None and execution.order.filled_quantity > 0 else 0
        exposure = execution.order.filled_quantity if execution is not None and execution.order is not None else Decimal("0")

        snap = build_snapshot(
            now=now,
            state=state,
            mode=mode,
            truth=obs.truth,
            controls=tuple(controls),
            open_orders=open_orders,
            fills=fills,
            positions=positions,
            exposure=exposure or Decimal("0"),
            alerts=len(alerts),
            incidents=len(self.incidents.open()),
            recon=recon,
            last_event=self.surv.last_event,
            ttl=self.config.freshness_ttl_seconds,
        )
        self.monitoring_repo.add(snap)

        operator, control = build_lanes(
            now=now,
            alerts=tuple(alerts),
            incidents=tuple(self.incidents.incidents),
            mode=mode,
            recon=recon,
            truth=obs.truth.value,
            accepted=bool(execution.receipt.accepted) if execution is not None else False,
            kill=obs.kill,
        )

        gov = None
        val = None
        if self.governance_enabled:
            gov = governance_packet(now=now, alerts=tuple(self.surv.alerts), incidents=tuple(self.incidents.incidents))
            val = validation_packet(now=now, alert_count=len(self.surv.alerts), incident_count=len(self.incidents.incidents))
            self.governance_repo.add(gov)

        evidence = self.evidence.compile(
            now=now,
            events=({"intake": intake.disposition.value, "reasons": list(intake.reasons)},),
            incidents=self.incidents.open(),
            truth=obs.truth,
        )
        self.evidence_repo.add(evidence)

        if operator_action:
            self.evidence.note(f"{now.isoformat()} operator {operator_action}")

        bundle = OperationalTruthBundle(
            occurred_at=now,
            intake=intake,
            snapshot=snap,
            operator_lane=operator,
            control_lane=control,
            alerts=tuple(alerts),
            incidents=tuple(self.incidents.open()),
            escalations=tuple(self.escalations[-8:]),
            remediation=tuple(self.tasks[-8:]),
            withdrawal=self.withdrawal.plan,
            control_requests=tuple(self.control_requests[-8:]),
            evidence=evidence,
            governance=gov,
            validation=val,
            execution_mode=mode,
            truth_source=obs.truth,
            broker_side_effect=False,
            mt5_used=False,
            durable=False,
        )
        self._last_bundle = self.publisher.publish(bundle)
        return self._last_bundle

    # --- queries ---

    def get_monitoring_snapshot(self):
        return self._last_bundle.snapshot if self._last_bundle else None

    def get_operator_lane(self):
        return self._last_bundle.operator_lane if self._last_bundle else None

    def get_control_lane(self):
        return self._last_bundle.control_lane if self._last_bundle else None

    def list_active_alerts(self) -> tuple[PostTradeAlert, ...]:
        return tuple(a for a in self.surv.alerts if not a.suppressed)

    def list_incidents(self) -> tuple[IncidentRecord, ...]:
        return tuple(self.incidents.incidents)

    def get_incident_timeline(self, incident_id) -> tuple[str, ...]:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            return ()
        return tuple(line for line in self.evidence.timeline if str(incident_id) in line or rec.incident_type.value in line)

    def list_open_remediation_tasks(self):
        return tuple(t for t in self.tasks if t.status == "open")

    def get_withdrawal_plan(self) -> OrderlyWithdrawalPlan | None:
        return self.withdrawal.plan

    def get_evidence_bundle(self):
        return self.evidence.bundles[-1] if self.evidence.bundles else None

    def get_governance_packet(self):
        return self._last_bundle.governance if self._last_bundle else None

    def get_validation_packet(self):
        return self._last_bundle.validation if self._last_bundle else None

    def get_operational_truth(self) -> OperationalTruthBundle | None:
        return self._last_bundle

    def classify_incident(self, incident_id, *, now=None) -> IncidentRecord:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            raise KeyError(incident_id)
        now = now or self.clock.now()
        nxt = rec if rec.state is not IncidentState.DETECTED else incident_transit(rec, IncidentState.TRIAGED, now=now)
        if nxt.state is IncidentState.TRIAGED:
            nxt = incident_transit(nxt, IncidentState.CLASSIFIED, now=now)
        self.incidents.replace(nxt)
        return nxt

    def contain_incident(self, incident_id, *, now=None) -> IncidentRecord:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            raise KeyError(incident_id)
        now = now or self.clock.now()
        cur = rec
        if cur.state is IncidentState.ESCALATED:
            cur = incident_transit(cur, IncidentState.CONTAINMENT_IN_PROGRESS, now=now)
        if cur.state is IncidentState.CONTAINMENT_IN_PROGRESS:
            cur = incident_transit(cur, IncidentState.CONTAINED, now=now, containment_status="contained")
        self.incidents.replace(cur)
        return cur

    def resolve_incident(self, incident_id, *, now=None) -> IncidentRecord:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            raise KeyError(incident_id)
        now = now or self.clock.now()
        cur = rec
        if cur.state is IncidentState.CONTAINED:
            cur = incident_transit(cur, IncidentState.RESOLVED, now=now, remediation_status="resolved")
        elif cur.state is IncidentState.REMEDIATION_IN_PROGRESS:
            cur = incident_transit(cur, IncidentState.RESOLVED, now=now, remediation_status="resolved")
        self.incidents.replace(cur)
        return cur

    def close_incident(self, incident_id, *, now=None, reason: str = "reviewed") -> IncidentRecord:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            raise KeyError(incident_id)
        now = now or self.clock.now()
        cur = rec
        if cur.state is IncidentState.RESOLVED:
            cur = incident_transit(cur, IncidentState.REVIEW_PENDING, now=now)
        if cur.state is IncidentState.REVIEW_PENDING:
            cur = incident_transit(cur, IncidentState.CLOSED, now=now, review_status=reason)
        self.incidents.replace(cur)
        return cur

    def transfer_incident(self, incident_id, *, now=None) -> IncidentRecord:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            raise KeyError(incident_id)
        now = now or self.clock.now()
        nxt = incident_transit(rec, IncidentState.TRANSFERRED_TO_PERSISTENCE, now=now)
        self.incidents.replace(nxt)
        return nxt

    def suppress_incident(self, incident_id, *, reason: str, now=None) -> IncidentRecord:
        rec = self.incidents.by_id(incident_id)
        if rec is None:
            raise KeyError(incident_id)
        if not reason.strip():
            raise ValueError("suppression requires a reason")
        return self.incidents.suppress(rec, now=now or self.clock.now(), reason=reason)

    def close_remediation(self, task_id, *, evidence: str):
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                nxt = close_task(task, evidence=evidence)
                self.tasks[i] = nxt
                return nxt
        raise KeyError(task_id)

    def approve_withdrawal(self) -> OrderlyWithdrawalPlan:
        return self.withdrawal.transit(WithdrawalState.APPROVAL_PENDING, now=self.clock.now())

    def initiate_withdrawal(self) -> OrderlyWithdrawalPlan:
        if self.withdrawal.plan and self.withdrawal.plan.state is WithdrawalState.RECOMMENDED:
            self.withdrawal.transit(WithdrawalState.APPROVAL_PENDING, now=self.clock.now())
        return self.withdrawal.transit(WithdrawalState.INITIATED, now=self.clock.now())

    def progress_withdrawal(self) -> OrderlyWithdrawalPlan:
        return self.withdrawal.transit(WithdrawalState.IN_PROGRESS, now=self.clock.now())

    def confirm_withdrawal(self) -> OrderlyWithdrawalPlan:
        return self.withdrawal.transit(WithdrawalState.CONFIRMED, now=self.clock.now(), confirmed=True)

    def complete_withdrawal(self) -> OrderlyWithdrawalPlan:
        return self.withdrawal.transit(WithdrawalState.COMPLETED, now=self.clock.now(), confirmed=True)

    def fail_withdrawal(self) -> OrderlyWithdrawalPlan:
        return self.withdrawal.transit(WithdrawalState.FAILED, now=self.clock.now())
