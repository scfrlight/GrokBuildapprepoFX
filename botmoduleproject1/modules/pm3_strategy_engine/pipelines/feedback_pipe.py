"""Synthetic feedback only. No MT5, no database."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy_engine import StrategyFeedbackEvent
from botmoduleproject1.modules.pm3_strategy_engine.application.health_service import HealthService
from botmoduleproject1.modules.pm3_strategy_engine.application.tracker_service import TrackerService


class FeedbackPipe:
    def __init__(self, trackers: TrackerService, health: HealthService) -> None:
        self.trackers = trackers
        self.health = health

    def ingest(self, event: StrategyFeedbackEvent):
        snap = self.trackers.apply_feedback(event)
        stale = not event.valid or event.kind == "inconsistent"
        invalid = event.kind == "invalid_config"
        health = self.health.snapshot(
            snap, event.occurred_at, invalid=invalid, stale_feedback=stale
        )
        return snap, health
