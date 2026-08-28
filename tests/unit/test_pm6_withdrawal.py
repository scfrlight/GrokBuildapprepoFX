import pytest

from botmoduleproject1.contracts.v1.post_trade import WithdrawalState
from botmoduleproject1.modules.pm6_post_trade.domain.errors import IllegalWithdrawalTransition
from tests.unit.test_pm6_incidents import _open_critical


def test_kill_recommends_withdrawal() -> None:
    pm6, _inc = _open_critical()
    plan = pm6.get_withdrawal_plan()
    assert plan is not None
    assert plan.state is WithdrawalState.RECOMMENDED
    assert plan.pm5_request is not None
    assert plan.pm5_request.broker_command is False
    assert plan.confirmed is False


def test_withdrawal_confirmation_required() -> None:
    pm6, _inc = _open_critical()
    pm6.approve_withdrawal()
    pm6.initiate_withdrawal()
    pm6.progress_withdrawal()
    with pytest.raises(IllegalWithdrawalTransition):
        pm6.withdrawal.transit(WithdrawalState.COMPLETED, now=pm6.clock.now(), confirmed=False)
    pm6.confirm_withdrawal()
    done = pm6.complete_withdrawal()
    assert done.state is WithdrawalState.COMPLETED
    assert done.confirmed is True


def test_failed_withdrawal_to_manual_review() -> None:
    pm6, _inc = _open_critical()
    pm6.approve_withdrawal()
    pm6.initiate_withdrawal()
    failed = pm6.fail_withdrawal()
    assert failed.state is WithdrawalState.FAILED
    nxt = pm6.withdrawal.transit(WithdrawalState.MANUAL_REVIEW, now=pm6.clock.now())
    assert nxt.state is WithdrawalState.MANUAL_REVIEW
