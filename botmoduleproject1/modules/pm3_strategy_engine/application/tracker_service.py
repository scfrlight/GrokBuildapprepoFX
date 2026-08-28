from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.strategy_engine import StrategyFeedbackEvent, TrackerSnapshot


class TrackerService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def snapshot(self, profile_id: str, version_id: str, as_of: datetime) -> TrackerSnapshot:
        current = self.repo.get(profile_id, version_id)
        if current is not None:
            return current
        created = TrackerSnapshot(
            profile_id=profile_id,
            version_id=version_id,
            as_of=as_of,
            insufficient_data=True,
            current_state="observe-only",
            trades_today=None,
            realized_r=None,
            win_rate=None,
        )
        self.repo.save(created)
        return created

    def note_intent(self, profile_id: str, version_id: str, as_of: datetime) -> TrackerSnapshot:
        snap = self.snapshot(profile_id, version_id, as_of)
        updated = snap.model_copy(
            update={
                "as_of": as_of,
                "signals_today": snap.signals_today + 1,
                "intents_today": snap.intents_today + 1,
                "insufficient_data": True,
            }
        )
        self.repo.save(updated)
        return updated

    def apply_feedback(self, event: StrategyFeedbackEvent) -> TrackerSnapshot:
        snap = self.snapshot(event.profile_id, event.version_id, event.occurred_at)
        if not event.valid:
            return snap.model_copy(
                update={"as_of": event.occurred_at, "current_state": "degraded_feedback"}
            )
        kind = event.kind
        extras: dict = {"as_of": event.occurred_at, "insufficient_data": True}
        if kind == "synthetic_fill":
            extras["trades_today"] = None  # still unknown / not real
        updated = snap.model_copy(update=extras)
        self.repo.save(updated)
        return updated
