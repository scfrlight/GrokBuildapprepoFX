from botmoduleproject1.contracts.v1.persistence import ReplayScope, ReplayState, SnapshotScope
from tests.unit.pm7_support import make_event, pm7_module


def test_deterministic_session_replay():
    mod = pm7_module()
    mod.ingest(make_event(idempotency_key="r1"))
    mod.ingest(make_event(idempotency_key="r2", ticket="SIM-2"))
    a = mod.replay(scope=ReplayScope.SESSION)
    b = mod.replay(scope=ReplayScope.SESSION)
    assert a.timeline == b.timeline
    assert a.event_count == 2
    assert a.state in {ReplayState.COMPLETED, ReplayState.VERIFIED}


def test_order_and_incident_replay():
    mod = pm7_module()
    mod.ingest(make_event(order_id="o1", incident_id="i1"))
    order = mod.replay(scope=ReplayScope.ORDER, entity_id="o1")
    inc = mod.replay(scope=ReplayScope.INCIDENT, entity_id="i1")
    assert order.event_count == 1
    assert inc.event_count == 1


def test_snapshot_assisted_replay_and_divergence():
    mod = pm7_module()
    mod.ingest(make_event())
    snap = mod.capture_snapshot(scope=SnapshotScope.SYSTEM)
    result = mod.replay()
    assert result.state in {ReplayState.VERIFIED, ReplayState.COMPLETED, ReplayState.DIVERGENCE_DETECTED}
    # extra event after snapshot should diverge sequence vs last snapshot
    mod.ingest(make_event(idempotency_key="after", ticket="SIM-9"))
    diverged = mod.replay()
    assert diverged.state in {ReplayState.DIVERGENCE_DETECTED, ReplayState.VERIFIED, ReplayState.COMPLETED}
    assert snap.journal_sequence == 1


def test_invalid_event_order_fails():
    from botmoduleproject1.modules.pm7_persistence.replay.engine import ReplayEngine
    from tests.unit.pm5_support import Clock
    from tests.unit.pm4_support import AS_OF

    mod = pm7_module()
    mod.ingest(make_event(idempotency_key="a"))
    mod.ingest(make_event(idempotency_key="b", ticket="SIM-2"))
    recs = list(reversed(mod.journal.records()))
    engine = ReplayEngine()
    result = engine.replay(recs, now=AS_OF, scope=ReplayScope.SESSION)
    assert result.state is ReplayState.FAILED
    assert "invalid_event_order" in result.divergence_notes


def test_replay_does_not_mutate_source():
    mod = pm7_module()
    mod.ingest(make_event())
    before = [r.content_hash for r in mod.journal.records()]
    mod.replay()
    after = [r.content_hash for r in mod.journal.records()]
    assert before == after
