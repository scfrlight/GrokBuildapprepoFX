from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import (
    IntegrityState,
    ReplayResult,
    ReplayScope,
    ReplayState,
)
from botmoduleproject1.modules.pm7_persistence.replay.divergence import compare_snapshot
from botmoduleproject1.modules.pm7_persistence.replay.timeline import timeline
from botmoduleproject1.modules.pm7_persistence.replay.validators import ordered


class ReplayEngine:
    def replay(self, records, *, now, scope: ReplayScope, snapshot=None, enabled: bool = True) -> ReplayResult:
        if not enabled:
            return ReplayResult(occurred_at=now, scope=scope, state=ReplayState.FAILED, divergence_notes=("replay_disabled",))
        if not records:
            return ReplayResult(occurred_at=now, scope=scope, state=ReplayState.FAILED, divergence_notes=("empty_chain",))
        if not ordered(records):
            return ReplayResult(
                occurred_at=now,
                scope=scope,
                state=ReplayState.FAILED,
                event_count=len(records),
                divergence_notes=("invalid_event_order",),
                source_lineage=tuple(str(r.event.event_id) for r in records),
            )
        reconstructed = {
            "journal_sequence": records[-1].sequence,
            "checksum": records[-1].content_hash,
            "count": len(records),
        }
        notes = []
        state = ReplayState.COMPLETED
        if snapshot is not None:
            notes = compare_snapshot(reconstructed, {"journal_sequence": snapshot.journal_sequence, "checksum": snapshot.payload.get("tip")})
            state = ReplayState.DIVERGENCE_DETECTED if notes else ReplayState.VERIFIED
        return ReplayResult(
            occurred_at=now,
            scope=scope,
            state=state,
            event_count=len(records),
            timeline=timeline(records),
            reconstructed=reconstructed,
            snapshot_comparison={"snapshot_id": str(snapshot.snapshot_id)} if snapshot is not None else {},
            divergence_notes=tuple(notes),
            verification=IntegrityState.VALID if state is ReplayState.VERIFIED else IntegrityState.WARNING if notes else IntegrityState.UNKNOWN,
            source_lineage=tuple(str(r.event.event_id) for r in records),
        )
