from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig
from tests.unit.pm5_support import Clock, ingest_allow
from tests.unit.pm6_support import pm6_module


def test_submit_burst_detector() -> None:
    cfg = Pm6PostTradeConfig(submit_burst=2, burst_window_seconds=60)
    pm6 = pm6_module(config=cfg)
    for i in range(4):
        _exe, bundle, pub = ingest_allow(key=f"burst-{i}")
        truth = pm6.observe(pub, bundle)
    assert any(a.detector == "submit_burst" for a in pm6.surv.alerts)
    assert any(i.incident_type.value == "monitoring_alert_burst" for i in pm6.list_incidents()) or truth.alerts


def test_reject_burst_detector() -> None:
    cfg = Pm6PostTradeConfig(reject_burst=2)
    pm6 = pm6_module(config=cfg)
    for i in range(4):
        _exe, bundle, pub = ingest_allow(key=f"rej-{i}")
        rejected = pub.model_copy(update={"receipt": pub.receipt.model_copy(update={"accepted": False})})
        pm6.observe(rejected, bundle)
    assert any(a.detector == "reject_burst" for a in pm6.surv.alerts)
