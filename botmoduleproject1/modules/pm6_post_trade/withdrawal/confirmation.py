from botmoduleproject1.contracts.v1.post_trade import WithdrawalState
from botmoduleproject1.modules.pm6_post_trade.withdrawal.planner import WithdrawalPlanner


def confirm(planner: WithdrawalPlanner, *, now):
    if planner.plan is None:
        raise ValueError("no plan")
    if planner.plan.state is WithdrawalState.IN_PROGRESS:
        planner.transit(WithdrawalState.CONFIRMED, now=now, confirmed=True)
    return planner.plan
