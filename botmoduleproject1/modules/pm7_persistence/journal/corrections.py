from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import JournalCategory, LedgerEvent, PersistenceTruthSource


def correction_event(original: LedgerEvent, *, payload: dict, actor: str, reason: str, now) -> LedgerEvent:
    return LedgerEvent(
        trace_id=original.trace_id,
        correlation_id=original.correlation_id,
        causation_id=original.event_id,
        session_id=original.session_id,
        source_module=original.source_module,
        source_entity_id=original.source_entity_id,
        event_type="correction",
        event_timestamp=now,
        ingested_at=now,
        source_timestamp=now,
        event_payload={"correction_of": str(original.event_id), "reason": reason, **payload},
        truth_source=PersistenceTruthSource.OPERATOR if actor else original.truth_source,
        lineage_refs=(str(original.event_id),),
        operator_id=actor,
        metadata={"reason": reason},
        category=JournalCategory.CORRECTION,
        ticket=original.ticket,
        symbol=original.symbol,
        order_id=original.order_id,
        strategy_id=original.strategy_id,
        incident_id=original.incident_id,
    )
