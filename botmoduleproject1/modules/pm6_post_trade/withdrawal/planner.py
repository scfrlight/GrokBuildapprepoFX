from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import (
    ControlRequest,
    ControlRequestKind,
    IncidentRecord,
    OrderlyWithdrawalPlan,
    SeverityLevel,
    WithdrawalState,
)
from botmoduleproject1.modules.pm6_post_trade.domain.errors import IllegalWithdrawalTransition
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id
from botmoduleproject1.modules.pm6_post_trade.domain.states import can_withdrawal


class WithdrawalPlanner:
    def __init__(self) -> None:
        self.plan: OrderlyWithdrawalPlan | None = None

    def recommend(self, incident: IncidentRecord, *, now: datetime, scope: str) -> OrderlyWithdrawalPlan:
        request = ControlRequest(
            request_id=new_id(),
            occurred_at=now,
            kind=ControlRequestKind.ORDERLY_WITHDRAWAL,
            scope=scope,
            reason=incident.detail or incident.incident_type.value,
            actor="pm6",
            approval_required=True,
            broker_command=False,
            status="recommended",
        )
        self.plan = OrderlyWithdrawalPlan(
            withdrawal_id=new_id(),
            occurred_at=now,
            scope=scope,
            trigger_reason=incident.incident_type.value,
            severity=incident.severity if incident.severity is not SeverityLevel.INFO else SeverityLevel.HIGH,
            steps=(
                "stop_new_activity",
                "request_pm5_freeze",
                "request_cancel_working",
                "enter_close_only",
                "wait_reconciliation",
                "manual_confirm",
            ),
            pm5_request=request,
            state=WithdrawalState.RECOMMENDED,
            confirmed=False,
        )
        return self.plan

    def transit(self, target: WithdrawalState, *, now: datetime, confirmed: bool = False) -> OrderlyWithdrawalPlan:
        if self.plan is None:
            raise IllegalWithdrawalTransition("no plan")
        if not can_withdrawal(self.plan.state, target):
            raise IllegalWithdrawalTransition(f"{self.plan.state.value} -> {target.value}")
        if target is WithdrawalState.COMPLETED and not (confirmed or self.plan.confirmed):
            raise IllegalWithdrawalTransition("confirmation required")
        self.plan = self.plan.model_copy(
            update={"state": target, "confirmed": self.plan.confirmed or confirmed, "occurred_at": now}
        )
        return self.plan
