from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import JournalCategory, LedgerEvent, PersistenceTruthSource
from botmoduleproject1.contracts.v1.post_trade import OperationalTruthBundle


_TRUTH = {
    "simulation_truth": PersistenceTruthSource.PM5_SIMULATION,
    "local_oms_truth": PersistenceTruthSource.PM5_LOCAL_OMS,
    "broker_truth": PersistenceTruthSource.PM5_BROKER,
    "unknown": PersistenceTruthSource.UNKNOWN,
    "stale": PersistenceTruthSource.UNKNOWN,
}


def from_monitoring(bundle: OperationalTruthBundle, *, now) -> LedgerEvent:
    truth = _TRUTH.get(bundle.truth_source.value, PersistenceTruthSource.PM6_MONITORING)
    if truth is PersistenceTruthSource.PM5_BROKER:
        # PM6 must not have labelled simulation as broker; force monitoring + unknown.
        truth = PersistenceTruthSource.PM6_MONITORING
    return LedgerEvent(
        event_id=bundle.bundle_id,
        trace_id=bundle.bundle_id,
        correlation_id=bundle.bundle_id,
        source_module="pm6_post_trade",
        source_entity_id=str(bundle.snapshot.monitoring_id) if getattr(bundle, "snapshot", None) is not None else None,
        event_type="operational_truth",
        event_timestamp=bundle.occurred_at,
        ingested_at=now,
        source_timestamp=bundle.occurred_at,
        event_payload={
            "producer": bundle.producer,
            "execution_mode": bundle.execution_mode,
            "incidents": len(bundle.incidents),
            "alerts": len(bundle.alerts),
            "durable": False,
        },
        truth_source=truth if truth is not PersistenceTruthSource.PM5_BROKER else PersistenceTruthSource.PM6_MONITORING,
        category=JournalCategory.SURVEILLANCE if not bundle.incidents else JournalCategory.INCIDENT,
        incident_id=str(bundle.incidents[0].incident_id) if bundle.incidents else None,
        idempotency_key=f"pm6:{bundle.bundle_id}",
    )
