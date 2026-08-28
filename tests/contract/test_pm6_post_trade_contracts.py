import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.post_trade import (
    ControlRequest,
    ControlRequestKind,
    IncidentState,
    IncidentType,
    MonitoringState,
    OperationalTruthBundle,
    OrderlyWithdrawalPlan,
    SeverityLevel,
    TruthSource,
    WithdrawalState,
)
from botmoduleproject1.contracts.v1.time import utc_now
from tests.unit.pm6_support import observe_allow


def test_required_enums() -> None:
    assert MonitoringState.DEGRADED
    assert IncidentState.ESCALATED
    assert IncidentType.KILL_STATE_BREACH
    assert TruthSource.SIMULATION_TRUTH
    assert WithdrawalState.RECOMMENDED


def test_control_request_cannot_be_broker_command() -> None:
    with pytest.raises(ValidationError):
        ControlRequest(
            occurred_at=utc_now(),
            kind=ControlRequestKind.FREEZE,
            reason="x",
            broker_command=True,
        )


def test_withdrawal_complete_requires_confirm() -> None:
    with pytest.raises(ValidationError):
        OrderlyWithdrawalPlan(
            occurred_at=utc_now(),
            scope="account",
            trigger_reason="test",
            severity=SeverityLevel.HIGH,
            state=WithdrawalState.COMPLETED,
            confirmed=False,
        )


def test_operational_truth_forbids_live_send() -> None:
    _m, _r, _p, truth = observe_allow(key="contract-ot")
    assert isinstance(truth, OperationalTruthBundle)
    payload = truth.model_dump()
    payload["broker_side_effect"] = True
    with pytest.raises(ValidationError):
        OperationalTruthBundle.model_validate(payload)
