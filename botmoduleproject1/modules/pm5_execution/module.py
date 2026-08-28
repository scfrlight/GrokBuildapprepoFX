"""PM5 Execution orchestrator. Simulation/shadow only. submit() always raises."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.execution import (
    BrokerAckEvent,
    BrokerEventType,
    ControlActionType,
    ControlScope,
    ExecutionIntentReceipt,
    ExecutionLifecycleState,
    ExecutionMode,
    ExecutionPublicationBundle,
    ExecutionRejectReason,
    ExecutionReport,
    FillEvent,
    OrderRecord,
    OrderRequest,
    Pm5OperatingState,
)
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.modules.pm5_execution.analytics.execution_quality import ExecutionQualityEngine
from botmoduleproject1.modules.pm5_execution.audit.registry import AuditRegistry
from botmoduleproject1.modules.pm5_execution.capabilities import PM5_EXECUTION_METADATA
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig, config_from_settings
from botmoduleproject1.modules.pm5_execution.control_plane.controller import ControlPlane
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id
from botmoduleproject1.modules.pm5_execution.ems.mt5_adapter import Mt5BrokerAdapter
from botmoduleproject1.modules.pm5_execution.ems.router import select_adapter
from botmoduleproject1.modules.pm5_execution.exposure.truth_service import ExposureTruthService
from botmoduleproject1.modules.pm5_execution.intake.gateway import ExecutionIntakeService
from botmoduleproject1.modules.pm5_execution.intake.normalizer import to_command
from botmoduleproject1.modules.pm5_execution.intake.validators import approved_quantity, validate_intake
from botmoduleproject1.modules.pm5_execution.manifest import module_manifest
from botmoduleproject1.modules.pm5_execution.observability.replay_log import ReplayService
from botmoduleproject1.modules.pm5_execution.oms.core import OrderLifecycleManager
from botmoduleproject1.modules.pm5_execution.oms.state_machine import IllegalTransition
from botmoduleproject1.modules.pm5_execution.publication.publisher import ExecutionPublicationService
from botmoduleproject1.modules.pm5_execution.reconciliation.engine import ReconciliationEngine
from botmoduleproject1.modules.pm5_execution.reliability.health import health_checks as pm5_health
from botmoduleproject1.modules.pm5_execution.surveillance.engine import SurveillanceEngine


class PM5ExecutionModule:
    """Registered as pm5_execution when enable_pm5_simulation is on."""

    def __init__(
        self,
        config: Pm5ExecutionConfig,
        clock: Any,
        *,
        simulation_enabled: bool = True,
        execution_flag: bool = False,
    ) -> None:
        self.config = config
        self.clock = clock
        self.simulation_enabled = simulation_enabled
        self.execution_flag = execution_flag
        self.mode = ExecutionMode.SIMULATION if simulation_enabled else ExecutionMode.DISABLED
        self.adapter = select_adapter(self.mode)
        self.mt5 = Mt5BrokerAdapter()
        self.oms = OrderLifecycleManager()
        self.control = ControlPlane(config)
        self.recon = ReconciliationEngine()
        self.surv = SurveillanceEngine(config)
        self.audit = AuditRegistry()
        self.replay = ReplayService()
        self.exposure = ExposureTruthService()
        self.quality = ExecutionQualityEngine()
        self.publisher = ExecutionPublicationService()
        self.intake = ExecutionIntakeService()
        self._last_recon = None
        self._fills: dict[str, list[FillEvent]] = {}
        self._commands: dict[str, Any] = {}
        self._submit_count = 0
        self._reject_count = 0

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM5ExecutionModule:
        flags = getattr(settings, "feature_flags")
        return cls(
            config_from_settings(settings),
            clock,
            simulation_enabled=bool(getattr(flags, "pm5_simulation", False)),
            execution_flag=bool(getattr(flags, "execution", False)),
        )

    def metadata(self) -> ModuleMetadata:
        return PM5_EXECUTION_METADATA

    def manifest(self) -> dict:
        return module_manifest()

    def is_ready(self) -> bool:
        return bool(self.simulation_enabled)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return pm5_health(
            kind,
            mode=self.mode,
            operating=self.control.operating,
            simulation_enabled=self.simulation_enabled,
            kill_latched=self.control.kill_latched,
        )

    def submit(self, request: OrderRequest) -> ExecutionReport:
        raise ExecutionDisabledError(
            "PM5 submit(OrderRequest) is disabled in Sequence 07. "
            "Simulation ingest records OMS state only. No MT5, no broker send."
        )

    def broker_submit(self, order_id) -> ExecutionIntentReceipt:
        rec = self.oms.get(order_id)
        return ExecutionIntentReceipt(
            accepted=False,
            order_id=order_id if rec else None,
            state=rec.state if rec else None,
            reasons=(
                ExecutionRejectReason.EXECUTION_NOT_PERMITTED,
                ExecutionRejectReason.BROKER_UNAVAILABLE,
            ),
            detail="execution_permitted=false; Sequence 07 has no broker path",
            broker_side_effect=False,
            simulation=True,
        )

    def ingest(
        self,
        bundle: RiskPublicationBundle | None,
        *,
        direction: Direction | None = None,
        entry_type: EntryType = EntryType.MARKET,
        quantity: Decimal | None = None,
        order_type: str = "market",
        entry_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        strategy_id: str | None = None,
        cluster: str | None = None,
    ) -> ExecutionPublicationBundle:
        now = self.clock.now()
        qty = quantity
        if bundle is not None and qty is None:
            qty = approved_quantity(bundle)
        symbol = bundle.symbol if bundle else None
        key = bundle.idempotency_key if bundle else None

        if key:
            existing = self.oms.by_key(key)
            if existing is not None:
                stored = self.oms.payload_for(key)
                incoming = (symbol, direction, qty)
                if stored == incoming:
                    return self._publish(
                        existing,
                        now,
                        accepted=True,
                        idempotent=True,
                        command=self._commands.get(str(existing.order_id)),
                    )
                reasons = (ExecutionRejectReason.DUPLICATE_CONFLICT,)
                self._reject_count += 1
                self.surv.note_reject(now)
                self.audit.record(now=now, kind="reject", summary="duplicate_conflict")
                return self._reject_bundle(now, existing, reasons, "conflicting payload for idempotency key")

        control_blocks = False
        if symbol:
            control_blocks = self.control.blocks(symbol, strategy_id, cluster)
        elif self.control.kill_latched or self.control.block_new:
            control_blocks = True

        reasons = validate_intake(
            bundle,
            now=now,
            config=self.config,
            direction=direction,
            quantity=qty,
            symbol=symbol,
            kill_blocks=self.control.kill_latched,
            control_blocks=control_blocks,
            mode=self.mode,
            feature_enabled=self.simulation_enabled,
            order_type=order_type,
            broker_path=False,
        )
        if reasons:
            self._reject_count += 1
            alert = self.surv.note_reject(now)
            if alert is not None and alert.automatic_protection and alert.detector == "reject_burst":
                self.control.emergency_cancel(now=now, reason=alert.detector, actor="surveillance")
            self.audit.record(
                now=now,
                kind="reject",
                summary=",".join(r.value for r in reasons),
            )
            if bundle is None or direction is None:
                return self._reject_bundle(now, None, tuple(reasons), "intake rejected")
            record = self._seed_record(
                bundle,
                direction=direction,
                entry_type=entry_type,
                qty=qty or Decimal("0"),
                entry_price=entry_price,
                stop_price=stop_price,
                now=now,
                state=ExecutionLifecycleState.INTENT_CREATED,
                reject_reason=reasons[0],
                detail=",".join(r.value for r in reasons),
            )
            record = self.oms.transit(
                record,
                ExecutionLifecycleState.REJECTED,
                now=now,
                reason=reasons[0].value,
                actor="intake",
                source="pm5",
                reject_reason=reasons[0],
                detail=record.detail,
            )
            self.replay.note_lifecycle(self.oms.events(record.order_id)[-1])
            return self._publish(record, now, accepted=False, reasons=tuple(reasons))

        assert bundle is not None and direction is not None and qty is not None
        record = self._seed_record(
            bundle,
            direction=direction,
            entry_type=entry_type,
            qty=qty,
            entry_price=entry_price,
            stop_price=stop_price,
            now=now,
            state=ExecutionLifecycleState.INTENT_CREATED,
        )
        record = self.oms.transit(
            record, ExecutionLifecycleState.VALIDATED, now=now, reason="intake_ok", actor="intake"
        )
        self.replay.note_lifecycle(self.oms.events(record.order_id)[-1])
        record = self.oms.transit(
            record, ExecutionLifecycleState.QUEUED, now=now, reason="queued", actor="oms"
        )
        self.replay.note_lifecycle(self.oms.events(record.order_id)[-1])

        self._submit_count += 1
        alert = self.surv.note_submit(now)
        if alert is not None and alert.automatic_protection:
            self.control.no_new_risk(now=now, reason=alert.detector, actor="surveillance")
            self.audit.incident(now=now, title=alert.detector, severity="high", detail=alert.recommended_action)

        record = self.oms.transit(
            record, ExecutionLifecycleState.SUBMITTED, now=now, reason="simulation_submit", actor="ems"
        )
        self.replay.note_lifecycle(self.oms.events(record.order_id)[-1])

        command = to_command(
            bundle,
            record,
            quantity=qty,
            order_type=order_type,
            entry_price=entry_price,
            stop_price=stop_price,
        )
        self._commands[str(record.order_id)] = command
        self.replay.append(
            record.order_id,
            {"kind": "normalized_command", "broker_eligible": False, "qty": str(qty)},
        )

        events = self.adapter.submit(command, now=now)
        for ev in events:
            if isinstance(ev, BrokerAckEvent) and ev.kind is BrokerEventType.SIMULATED_ACK:
                record = self.oms.transit(
                    record,
                    ExecutionLifecycleState.ACKNOWLEDGED,
                    now=now,
                    reason="simulated_ack",
                    actor="simulation_adapter",
                    source="ems",
                    broker_ticket=ev.ticket,
                )
                self.replay.note_lifecycle(self.oms.events(record.order_id)[-1])
            elif isinstance(ev, FillEvent):
                if not self.config.simulation_auto_fill:
                    continue
                record = self.oms.apply_fill(record, ev, now=now)
                self._fills.setdefault(str(record.order_id), []).append(ev)
                self.replay.append(
                    record.order_id,
                    {
                        "kind": "fill",
                        "source": ev.source,
                        "qty": str(ev.quantity),
                        "ticket": ev.ticket,
                    },
                )
            elif isinstance(ev, BrokerAckEvent) and ev.kind is BrokerEventType.DISABLED:
                record = self.oms.transit(
                    record,
                    ExecutionLifecycleState.BLOCKED,
                    now=now,
                    reason="adapter_disabled",
                    actor="disabled_adapter",
                    source="ems",
                )

        if record.state is ExecutionLifecycleState.FILLED:
            record = self.oms.transit(
                record,
                ExecutionLifecycleState.RECONCILIATION_PENDING,
                now=now,
                reason="awaiting_broker_truth",
                actor="recon",
            )
            self.replay.note_lifecycle(self.oms.events(record.order_id)[-1])

        self._last_recon = self.recon.run(
            now=now,
            local_order_count=len(self.oms.all_orders()),
            broker_order_count=0,
            broker_truth_available=False,
        )
        self.audit.record(now=now, kind="ingest", summary=f"accepted {record.order_id}")
        return self._publish(record, now, accepted=True, command=command)

    def cancel_order(self, order_id, *, reason: str = "operator_cancel", actor: str = "operator"):
        now = self.clock.now()
        rec = self.oms.get(order_id)
        if rec is None:
            return None
        alert = self.surv.note_cancel(now)
        if alert is not None:
            self.control.no_new_risk(now=now, reason=alert.detector, actor="surveillance")
        command = self._commands.get(str(order_id))
        rec = self.oms.transit(
            rec,
            ExecutionLifecycleState.CANCEL_REQUESTED,
            now=now,
            reason=reason,
            actor=actor,
            source="control_plane",
        )
        if command is not None:
            self.adapter.cancel(command, now=now)
        rec = self.oms.transit(
            rec,
            ExecutionLifecycleState.CANCELLED,
            now=now,
            reason="simulation_cancel",
            actor="simulation_adapter",
            source="ems",
        )
        self.control._record(
            now,
            ControlActionType.CANCEL_ORDER,
            ControlScope.SYMBOL,
            reason,
            actor,
            "control_plane",
            rec.symbol,
            affected=(rec.order_id,),
        )
        return rec

    def freeze_scope(self, *, scope, reason: str, actor: str = "operator", scope_id: str | None = None):
        return self.control.freeze(
            now=self.clock.now(), scope=scope, reason=reason, actor=actor, scope_id=scope_id
        )

    def enter_close_only(self, *, reason: str, actor: str = "operator"):
        return self.control.enter_close_only(now=self.clock.now(), reason=reason, actor=actor)

    def no_new_risk(self, *, reason: str, actor: str = "operator"):
        return self.control.no_new_risk(now=self.clock.now(), reason=reason, actor=actor)

    def emergency_cancel(self, *, reason: str, actor: str = "operator"):
        now = self.clock.now()
        working = [
            o.order_id
            for o in self.oms.all_orders()
            if o.state
            in {
                ExecutionLifecycleState.QUEUED,
                ExecutionLifecycleState.SUBMITTED,
                ExecutionLifecycleState.ACKNOWLEDGED,
                ExecutionLifecycleState.PARTIALLY_FILLED,
            }
        ]
        rec = self.control.emergency_cancel(now=now, reason=reason, actor=actor, affected=working)
        for oid in working:
            try:
                self.cancel_order(oid, reason="emergency_cancel", actor=actor)
            except IllegalTransition:
                continue
        self.audit.incident(now=now, title="emergency_cancel", severity="critical", detail=reason)
        return rec

    def request_recovery(self, *, reason: str, actor: str = "operator"):
        return self.control.recover(now=self.clock.now(), reason=reason, actor=actor)

    def get_order(self, order_id) -> OrderRecord | None:
        return self.oms.get(order_id)

    def get_order_timeline(self, order_id):
        return self.oms.events(order_id)

    def list_working_orders(self) -> tuple[OrderRecord, ...]:
        working = {
            ExecutionLifecycleState.QUEUED,
            ExecutionLifecycleState.SUBMITTED,
            ExecutionLifecycleState.ACKNOWLEDGED,
            ExecutionLifecycleState.PARTIALLY_FILLED,
            ExecutionLifecycleState.RECONCILIATION_PENDING,
        }
        return tuple(o for o in self.oms.all_orders() if o.state in working)

    def get_exposure(self):
        now = self.clock.now()
        return self.exposure.snapshot(self.oms.all_orders(), now=now, recon=self._last_recon)

    def get_reconciliation_status(self):
        if self._last_recon is not None:
            return self._last_recon
        return self.recon.run(
            now=self.clock.now(),
            local_order_count=len(self.oms.all_orders()),
            broker_order_count=0,
            broker_truth_available=False,
        )

    def get_replay_bundle(self, order_id):
        return self.replay.bundle(order_id)

    def get_control_state(self) -> dict[str, Any]:
        return {
            "operating": self.control.operating.value,
            "block_new": self.control.block_new,
            "close_only": self.control.close_only,
            "kill_latched": self.control.kill_latched,
            "mode": self.mode.value,
        }

    def _seed_record(
        self,
        bundle: RiskPublicationBundle,
        *,
        direction: Direction,
        entry_type: EntryType,
        qty: Decimal,
        entry_price,
        stop_price,
        now,
        state: ExecutionLifecycleState,
        reject_reason=None,
        detail: str = "",
    ) -> OrderRecord:
        from botmoduleproject1.contracts.v1.execution import OrderLifecycleEvent

        record = OrderRecord(
            order_id=new_id(),
            intent_id=bundle.intent_id,
            pm4_decision_id=bundle.verdict.verdict_id,
            idempotency_key=bundle.idempotency_key or str(new_id()),
            correlation_id=bundle.correlation_id,
            causation_id=bundle.causation_id,
            occurred_at=now,
            symbol=bundle.symbol,
            direction=direction,
            entry_type=entry_type,
            original_quantity=qty,
            remaining_quantity=qty,
            filled_quantity=Decimal("0"),
            state=state,
            simulation=True,
            broker_side_effect=False,
            entry_price=entry_price,
            stop_price=stop_price,
            reject_reason=reject_reason,
            detail=detail,
        )
        event = OrderLifecycleEvent(
            event_id=new_id(),
            order_id=record.order_id,
            occurred_at=now,
            from_state=None,
            to_state=state,
            reason="created",
            actor="intake",
            source="pm5",
            correlation_id=record.correlation_id,
        )
        self.oms.put_new(record, event)
        self.replay.note_lifecycle(event)
        return record

    def _reject_bundle(self, now, order, reasons, detail: str) -> ExecutionPublicationBundle:
        receipt = ExecutionIntentReceipt(
            accepted=False,
            order_id=None if order is None else order.order_id,
            state=None if order is None else order.state,
            reasons=reasons,
            detail=detail,
            broker_side_effect=False,
            simulation=True,
        )
        recon = self.recon.run(
            now=now,
            local_order_count=len(self.oms.all_orders()),
            broker_order_count=0,
            broker_truth_available=False,
        )
        self._last_recon = recon
        return self.publisher.build(
            now=now,
            receipt=receipt,
            order=order,
            command=None,
            lifecycle=() if order is None else self.oms.events(order.order_id),
            fills=(),
            control=self.control.actions,
            recon=recon,
            exposure=self.exposure.snapshot(self.oms.all_orders(), now=now, recon=recon),
            quality=self.quality.report(order, () if order is None else self.oms.events(order.order_id), (), now=now, rejects=self._reject_count, submits=self._submit_count),
            alerts=self.surv.alerts,
            operating=self.control.operating if self.control.operating is not Pm5OperatingState.NORMAL else Pm5OperatingState.DEGRADED,
            mode=self.mode,
        )

    def _publish(
        self,
        record: OrderRecord,
        now,
        *,
        accepted: bool,
        reasons: tuple = (),
        command=None,
        idempotent: bool = False,
    ) -> ExecutionPublicationBundle:
        fills = tuple(self._fills.get(str(record.order_id), ()))
        lifecycle = self.oms.events(record.order_id)
        recon = self._last_recon or self.recon.run(
            now=now,
            local_order_count=len(self.oms.all_orders()),
            broker_order_count=0,
            broker_truth_available=False,
        )
        self._last_recon = recon
        receipt = ExecutionIntentReceipt(
            accepted=accepted,
            order_id=record.order_id,
            state=record.state,
            reasons=reasons,
            detail=record.detail,
            broker_side_effect=False,
            simulation=True,
            idempotent_replay=idempotent,
        )
        operating = self.control.operating
        if operating is Pm5OperatingState.NORMAL:
            operating = Pm5OperatingState.DEGRADED
        return self.publisher.build(
            now=now,
            receipt=receipt,
            order=record,
            command=command or self._commands.get(str(record.order_id)),
            lifecycle=lifecycle,
            fills=fills,
            control=self.control.actions,
            recon=recon,
            exposure=self.exposure.snapshot(self.oms.all_orders(), now=now, recon=recon),
            quality=self.quality.report(
                record, lifecycle, fills, now=now, rejects=self._reject_count, submits=self._submit_count
            ),
            alerts=self.surv.alerts,
            operating=operating,
            mode=self.mode,
        )
