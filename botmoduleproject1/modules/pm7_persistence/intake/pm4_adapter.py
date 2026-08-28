from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import JournalCategory, LedgerEvent, PersistenceTruthSource
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle


def from_risk(bundle: RiskPublicationBundle, *, now) -> LedgerEvent:
    verdict = bundle.verdict
    return LedgerEvent(
        event_id=bundle.bundle_id,
        trace_id=verdict.correlation_id,
        correlation_id=verdict.correlation_id,
        causation_id=verdict.causation_id,
        source_module="pm4_risk_gate",
        source_entity_id=str(verdict.intent_id),
        event_type="risk_publication",
        event_timestamp=bundle.occurred_at,
        ingested_at=now,
        source_timestamp=bundle.occurred_at,
        event_payload={
            "status": verdict.status.value,
            "producer": bundle.producer,
            "execution_permitted": getattr(bundle, "execution_permitted", False),
        },
        truth_source=PersistenceTruthSource.PM4_RISK,
        category=JournalCategory.RISK_DECISION,
        idempotency_key=f"pm4:{bundle.bundle_id}",
    )
