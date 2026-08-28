from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import (
    EscalationAction,
    EscalationRoute,
    IncidentRecord,
    SeverityLevel,
)
from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id


def escalate(incident: IncidentRecord, *, now: datetime, config: Pm6PostTradeConfig) -> EscalationAction:
    if incident.severity is SeverityLevel.CRITICAL:
        route, deadline, role = EscalationRoute.IMMEDIATE, config.escalation_critical_seconds, "risk_officer"
    elif incident.severity is SeverityLevel.HIGH:
        route, deadline, role = EscalationRoute.SAME_SESSION, config.escalation_high_seconds, "desk_lead"
    elif incident.severity is SeverityLevel.MEDIUM:
        route, deadline, role = EscalationRoute.SAME_DAY, 3600, "operator"
    else:
        route, deadline, role = EscalationRoute.SCHEDULED_REVIEW, 86400, "governance"
    return EscalationAction(
        escalation_id=new_id(),
        occurred_at=now,
        route=route,
        target_role=role,
        incident_id=incident.incident_id,
        required_response="acknowledge_and_contain" if incident.severity is SeverityLevel.CRITICAL else "review",
        deadline_seconds=deadline,
        severity=incident.severity,
        reason=incident.detail or incident.incident_type.value,
    )
