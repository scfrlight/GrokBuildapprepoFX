from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import IncidentRecord, IncidentState
from botmoduleproject1.modules.pm6_post_trade.domain.errors import IllegalIncidentTransition
from botmoduleproject1.modules.pm6_post_trade.domain.states import can_incident


def transit(record: IncidentRecord, target: IncidentState, *, now: datetime, **updates) -> IncidentRecord:
    if not can_incident(record.state, target):
        raise IllegalIncidentTransition(f"{record.state.value} -> {target.value} is illegal")
    return record.model_copy(update={"state": target, "updated_at": now, **updates})
