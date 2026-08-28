from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import (
    EvidenceBundle,
    EvidenceState,
    IntegrityState,
    PersistenceTruthSource,
)


def build_bundle(*, now, records, integrity: IntegrityState, entity_id=None, actor=None) -> EvidenceBundle:
    events = [r.event for r in records]
    missing = []
    if not events:
        missing.append("no_source_events")
    truth = events[-1].truth_source if events else PersistenceTruthSource.UNKNOWN
    timeline = tuple(f"{r.sequence}:{r.event.event_type}:{r.event.source_module}" for r in records)
    lineage = tuple(str(r.event.event_id) for r in records)
    summary = (
        f"{len(records)} committed events. truth={truth.value}. integrity={integrity.value}."
        if records
        else "insufficient_data"
    )
    return EvidenceBundle(
        occurred_at=now,
        when=now,
        state=EvidenceState.ASSEMBLED if records else EvidenceState.DRAFT,
        what="journal_evidence",
        module="pm7_persistence",
        entity_id=entity_id,
        changed="append_only_journal",
        why="canonical_memory",
        actor=actor,
        result="assembled" if records else "insufficient_data",
        unresolved=tuple(missing),
        truth_source=truth,
        integrity_status=integrity,
        source_event_ids=lineage,
        timeline=timeline,
        lineage_refs=lineage,
        summary=summary,
        payload={"event_count": len(records), "notes": missing},
        durable=False,
    )
