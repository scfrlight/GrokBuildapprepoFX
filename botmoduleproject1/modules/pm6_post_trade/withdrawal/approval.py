from botmoduleproject1.contracts.v1.post_trade import WithdrawalState
from botmoduleproject1.modules.pm6_post_trade.withdrawal.planner import WithdrawalPlanner


def request_approval(planner: WithdrawalPlanner, *, now):
    return planner.transit(WithdrawalState.APPROVAL_PENDING, now=now)
