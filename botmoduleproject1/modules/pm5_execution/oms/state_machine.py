from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.execution import ExecutionLifecycleState, OrderLifecycleEvent, OrderRecord
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id
from botmoduleproject1.modules.pm5_execution.domain.states import TERMINAL, can_transition


class IllegalTransition(ValueError):
    pass


def apply_transition(
    record: OrderRecord,
    target: ExecutionLifecycleState,
    *,
    now: datetime,
    reason: str,
    actor: str,
    source: str = "oms",
    attributes: dict | None = None,
    **updates,
) -> tuple[OrderRecord, OrderLifecycleEvent]:
    if record.state in TERMINAL:
        raise IllegalTransition(f"terminal state {record.state.value} cannot move")
    if record.state is target and target is ExecutionLifecycleState.PARTIALLY_FILLED:
        pass
    elif not can_transition(record.state, target):
        raise IllegalTransition(f"{record.state.value} -> {target.value} is illegal")
    event = OrderLifecycleEvent(
        event_id=new_id(),
        order_id=record.order_id,
        occurred_at=now,
        from_state=record.state,
        to_state=target,
        reason=reason,
        actor=actor,
        source=source,
        correlation_id=record.correlation_id,
        attributes=attributes or {},
    )
    nxt = record.model_copy(update={"state": target, **updates})
    return nxt, event
