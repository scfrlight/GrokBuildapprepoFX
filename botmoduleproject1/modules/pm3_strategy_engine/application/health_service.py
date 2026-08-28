from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.strategy_engine import HealthStatus, ProfileHealthSnapshot, TrackerSnapshot
from botmoduleproject1.modules.pm3_strategy_engine.domain.policies import default_health


class DefaultHealthPolicy:
    def evaluate(
        self, tracker: TrackerSnapshot, *, invalid: bool = False, stale_feedback: bool = False
    ) -> HealthStatus:
        samples = tracker.intents_today
        return default_health(samples=samples, invalid=invalid, stale_feedback=stale_feedback)


class HealthService:
    def __init__(self, policy: DefaultHealthPolicy | None = None) -> None:
        self.policy = policy or DefaultHealthPolicy()

    def snapshot(
        self,
        tracker: TrackerSnapshot,
        as_of: datetime,
        *,
        invalid: bool = False,
        stale_feedback: bool = False,
    ) -> ProfileHealthSnapshot:
        status = self.policy.evaluate(tracker, invalid=invalid, stale_feedback=stale_feedback)
        action = "observe"
        if status is HealthStatus.DISABLED:
            action = "disable_voting"
        elif status is HealthStatus.DEGRADED:
            action = "suppress_until_consistent"
        return ProfileHealthSnapshot(
            profile_id=tracker.profile_id,
            version_id=tracker.version_id,
            as_of=as_of,
            health_status=status,
            degradation_triggers=(("invalid_config",) if invalid else ())
            + (("stale_feedback",) if stale_feedback else ()),
            recommended_action=action,
            last_updated_at=as_of,
        )
