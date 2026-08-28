from botmoduleproject1.contracts.v1.persistence import AnalyticsDataset, DataQualityStatus, PersistenceTruthSource
from botmoduleproject1.modules.pm7_persistence.warehouse.lineage import event_ids
from botmoduleproject1.modules.pm7_persistence.warehouse.transforms import counts


def build_dataset(*, now, records, scope: str) -> AnalyticsDataset:
    if not records:
        return AnalyticsDataset(
            occurred_at=now,
            scope=scope,
            quality=DataQualityStatus.INSUFFICIENT_DATA,
            metrics={"event_count": 0},
            metric_definitions={"event_count": "committed journal events"},
        )
    sim = sum(1 for r in records if r.event.ticket and r.event.ticket.startswith("SIM-"))
    return AnalyticsDataset(
        occurred_at=now,
        scope=scope,
        source_event_ids=event_ids(records),
        metrics={
            "event_count": len(records),
            "simulation_tickets": sim,
            "by_module": counts(records),
            "broker_fills": None,
        },
        metric_definitions={
            "event_count": "committed journal events",
            "simulation_tickets": "SIM-* count; not broker fills",
            "broker_fills": "not_available without venue",
        },
        quality=DataQualityStatus.OK if records else DataQualityStatus.INSUFFICIENT_DATA,
        truth_source=PersistenceTruthSource.DERIVED,
    )
