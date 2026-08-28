from botmoduleproject1.contracts.v1.post_trade import GovernanceReviewState
from tests.unit.pm6_support import observe_allow


def test_governance_and_validation_packets() -> None:
    pm6, _r, _p, truth = observe_allow(key="gov-1")
    gov = pm6.get_governance_packet()
    val = pm6.get_validation_packet()
    assert gov is not None
    assert val is not None
    assert gov.state is GovernanceReviewState.SCHEDULED
    assert val.alert_precision == "insufficient_data"
    assert val.false_positive == "insufficient_data"
    ev = pm6.get_evidence_bundle()
    assert ev is not None
    assert ev.durable is False
    assert ev.persistence_handoff == "non_durable_before_pm7"
    assert ev.fingerprint
    assert truth.governance is gov
