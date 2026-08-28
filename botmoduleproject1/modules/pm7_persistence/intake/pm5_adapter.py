from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import ExecutionPublicationBundle, ReconciliationOutcome
from botmoduleproject1.contracts.v1.persistence import (
    JournalCategory,
    LedgerEvent,
    PersistenceTruthSource,
    ReconciliationPersistRecord,
    ReconciliationPersistState,
)


def from_execution(bundle: ExecutionPublicationBundle, *, now) -> LedgerEvent:
    order = bundle.order
    ticket = order.broker_ticket if order is not None else None
    truth = PersistenceTruthSource.PM5_SIMULATION if (ticket or "").startswith("SIM-") else PersistenceTruthSource.PM5_LOCAL_OMS
    if bundle.execution_mode.value in {"simulation", "shadow"}:
        truth = PersistenceTruthSource.PM5_SIMULATION
    return LedgerEvent(
        event_id=bundle.bundle_id,
        trace_id=order.correlation_id if order is not None else bundle.bundle_id,
        correlation_id=order.correlation_id if order is not None else bundle.bundle_id,
        causation_id=order.causation_id if order is not None else None,
        source_module="pm5_execution",
        source_entity_id=str(order.order_id) if order is not None else None,
        event_type="execution_publication",
        event_timestamp=bundle.occurred_at,
        ingested_at=now,
        source_timestamp=bundle.occurred_at,
        event_payload={
            "producer": bundle.producer,
            "execution_mode": bundle.execution_mode.value,
            "operating_state": bundle.operating_state.value,
            "ticket": ticket,
            "simulation": True if order is None else order.simulation,
            "mt5_used": False,
            "broker_side_effect": False,
        },
        truth_source=truth,
        category=JournalCategory.ORDER_LIFECYCLE,
        ticket=ticket,
        symbol=order.symbol if order is not None else None,
        order_id=str(order.order_id) if order is not None else None,
        idempotency_key=f"pm5:{bundle.bundle_id}",
    )


def recon_from_execution(bundle: ExecutionPublicationBundle, *, now, source_event_id) -> ReconciliationPersistRecord | None:
    rec = bundle.reconciliation
    if rec is None:
        return ReconciliationPersistRecord(
            occurred_at=now,
            order_id=str(bundle.order.order_id) if bundle.order is not None else None,
            symbol=bundle.order.symbol if bundle.order is not None else None,
            state=ReconciliationPersistState.UNAVAILABLE,
            broker_truth_available=False,
            truth_source=PersistenceTruthSource.PM5_SIMULATION,
            source_event_id=source_event_id,
            notes="no venue; reconciliation unavailable",
        )
    mapping = {
        ReconciliationOutcome.PASS: ReconciliationPersistState.PASS,
        ReconciliationOutcome.MISMATCH: ReconciliationPersistState.MISMATCH,
        ReconciliationOutcome.DEGRADED: ReconciliationPersistState.DEGRADED,
        ReconciliationOutcome.CRITICAL: ReconciliationPersistState.CRITICAL,
    }
    state = mapping.get(rec.outcome, ReconciliationPersistState.DEGRADED)
    if not rec.broker_truth_available and state is ReconciliationPersistState.PASS:
        state = ReconciliationPersistState.DEGRADED
        notes = "no venue; pass rewritten to degraded"
    else:
        notes = rec.notes or rec.recommended_action
    return ReconciliationPersistRecord(
        occurred_at=rec.as_of,
        order_id=str(bundle.order.order_id) if bundle.order is not None else None,
        symbol=bundle.order.symbol if bundle.order is not None else None,
        state=state,
        broker_truth_available=bool(rec.broker_truth_available),
        truth_source=PersistenceTruthSource.PM5_SIMULATION
        if not rec.broker_truth_available
        else PersistenceTruthSource.PM5_BROKER,
        source_event_id=source_event_id,
        notes=notes or "",
        local_state=dict(rec.local_state),
        broker_state=dict(rec.broker_state),
    )
