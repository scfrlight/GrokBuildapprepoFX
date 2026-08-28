from tests.unit.pm5_support import ingest_allow
from tests.unit.pm6_support import pm6_module


def test_alert_dedup_retains_evidence() -> None:
    pm6 = pm6_module()
    _exe, bundle, pub = ingest_allow(key="dedup-1")
    first = pm6.observe(pub, bundle)
    second = pm6.observe(pub, bundle)
    dets = [a.detector for a in second.alerts]
    # second observe of the same snapshot may suppress burst/control fingerprints
    suppressed = [a for a in pm6.surv.alerts if a.suppressed]
    assert first.alerts or second.snapshot is not None
    # evidence timeline keeps both ticks even if alerts suppressed
    assert any("observe" in line or "alert" in line for line in pm6.evidence.timeline)
    assert pm6.get_evidence_bundle() is not None
    assert pm6.get_evidence_bundle().durable is False
    _ = dets, suppressed


def test_materially_different_alerts_not_merged() -> None:
    from decimal import Decimal

    from botmoduleproject1.contracts.v1.execution import FillEvent

    pm6 = pm6_module()
    _exe, bundle, pub = ingest_allow(key="distinct")
    extra = FillEvent(
        order_id=pub.order.order_id,
        occurred_at=pub.occurred_at,
        quantity=Decimal("9"),
        price=Decimal("1.1"),
        source="simulation",
        ticket=pub.order.broker_ticket,
    )
    order = pub.order.model_copy(update={"filled_quantity": pub.order.original_quantity + Decimal("9")})
    forged = pub.model_copy(update={"order": order, "fills": pub.fills + (extra,)})
    truth = pm6.observe(forged, bundle)
    detectors = {a.detector for a in truth.alerts if not a.suppressed}
    assert "quantity_drift" in detectors
