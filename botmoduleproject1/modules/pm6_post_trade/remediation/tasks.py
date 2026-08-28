from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import IncidentRecord, RemediationTask, SeverityLevel
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id


def open_task(incident: IncidentRecord, *, now: datetime) -> RemediationTask:
    return RemediationTask(
        task_id=new_id(),
        occurred_at=now,
        incident_id=incident.incident_id,
        action=incident.detail or incident.incident_type.value,
        owner=incident.owner,
        priority=incident.severity,
        due_seconds=0 if incident.severity is SeverityLevel.CRITICAL else 300,
        closure_criteria=incident.closure_criteria,
        status="open",
        evidence_required=True,
    )


def close_task(task: RemediationTask, *, evidence: str) -> RemediationTask:
    if not evidence.strip():
        return task.model_copy(update={"status": "evidence_required"})
    return task.model_copy(update={"status": "closed"})
