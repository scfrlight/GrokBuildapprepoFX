from botmoduleproject1.contracts.v1.persistence import (
    PersistenceTruthSource,
    ReconciliationPersistRecord,
    ReconciliationPersistState,
)
from tests.unit.pm4_support import AS_OF
from tests.unit.pm7_support import ingest_sim, pm7_module


def _rec(state, *, broker=False, order_id="ord-1"):
    kwargs = dict(
        occurred_at=AS_OF,
        order_id=order_id,
        session_id="sess-1",
        symbol="EURUSD",
        state=state,
        broker_truth_available=broker,
        truth_source=PersistenceTruthSource.PM5_BROKER if broker else PersistenceTruthSource.PM5_SIMULATION,
    )
    return ReconciliationPersistRecord.model_validate(kwargs)


def test_store_pass_with_venue():
    rec = _rec(ReconciliationPersistState.PASS, broker=True)
    assert rec.state is ReconciliationPersistState.PASS


def test_store_mismatch():
    mod = pm7_module()
    stored = mod.record_reconciliation(_rec(ReconciliationPersistState.MISMATCH))
    assert stored.state is ReconciliationPersistState.MISMATCH


def test_store_degraded():
    mod = pm7_module()
    stored = mod.record_reconciliation(_rec(ReconciliationPersistState.DEGRADED))
    assert stored.state is ReconciliationPersistState.DEGRADED


def test_store_unavailable():
    mod = pm7_module()
    stored = mod.record_reconciliation(_rec(ReconciliationPersistState.UNAVAILABLE))
    assert stored.state is ReconciliationPersistState.UNAVAILABLE


def test_store_critical():
    mod = pm7_module()
    stored = mod.record_reconciliation(_rec(ReconciliationPersistState.CRITICAL))
    assert stored.state is ReconciliationPersistState.CRITICAL


def test_resolution_event_keeps_history():
    mod = pm7_module()
    mod.record_reconciliation(_rec(ReconciliationPersistState.MISMATCH))
    mod.record_reconciliation(_rec(ReconciliationPersistState.RESOLVED))
    hist = mod.get_reconciliation_history(order_id="ord-1")
    assert len(hist) == 2
    assert hist[0].state is ReconciliationPersistState.MISMATCH


def test_query_by_order_session_symbol():
    mod = pm7_module()
    mod.record_reconciliation(_rec(ReconciliationPersistState.DEGRADED, order_id="a"))
    assert mod.recon.history(order_id="a")
    assert mod.recon.history(symbol="EURUSD")
    assert mod.recon.history(session_id="sess-1")


def test_ingest_pm5_never_silent_pass():
    _mod, _b, _p, _r = ingest_sim(key="recon-pass")
    hist = _mod.get_reconciliation_history()
    assert all(h.state is not ReconciliationPersistState.PASS or h.broker_truth_available for h in hist)
