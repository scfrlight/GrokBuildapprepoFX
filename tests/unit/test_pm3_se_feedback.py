from botmoduleproject1.contracts.v1.strategy_engine import HealthStatus, StrategyFeedbackEvent
from tests.unit.pm3se_support import AS_OF, engine


def test_synthetic_feedback_does_not_claim_health() -> None:
    mod = engine()
    profile = mod.profiles.list_all()[0]
    event = StrategyFeedbackEvent(
        occurred_at=AS_OF,
        symbol="EURUSD",
        profile_id=profile.profile_id,
        version_id=profile.active_version_id or "v",
        kind="synthetic_fill",
        payload={"r": 0.5},
        valid=True,
    )
    snap, health = mod.ingest_feedback(event)
    assert snap.insufficient_data is True
    assert snap.win_rate is None
    assert snap.trades_today is None
    assert health.health_status in {HealthStatus.UNKNOWN, HealthStatus.WATCHLIST}


def test_invalid_feedback_degrades() -> None:
    mod = engine()
    profile = mod.profiles.list_all()[0]
    event = StrategyFeedbackEvent(
        occurred_at=AS_OF,
        symbol="EURUSD",
        profile_id=profile.profile_id,
        version_id=profile.active_version_id or "v",
        kind="inconsistent",
        payload={},
        valid=False,
    )
    snap, health = mod.ingest_feedback(event)
    assert health.health_status is HealthStatus.DEGRADED
    assert snap.current_state == "degraded_feedback"
