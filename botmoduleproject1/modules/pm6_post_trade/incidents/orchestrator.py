from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import (
    IncidentRecord,
    IncidentState,
    PostTradeAlert,
    SeverityLevel,
    TruthSource,
)
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id
from botmoduleproject1.modules.pm6_post_trade.incidents.classifier import classify
from botmoduleproject1.modules.pm6_post_trade.incidents.lifecycle import transit
from botmoduleproject1.modules.pm6_post_trade.monitoring.findings import Finding


class IncidentOrchestrator:
    def __init__(self) -> None:
        self.incidents: list[IncidentRecord] = []

    def open_from(self, finding: Finding, alert: PostTradeAlert, *, now: datetime, truth: TruthSource) -> IncidentRecord:
        itype, category, severity = classify(finding)
        rec = IncidentRecord(
            incident_id=new_id(),
            occurred_at=now,
            updated_at=now,
            incident_type=itype,
            category=category,
            severity=severity,
            state=IncidentState.DETECTED,
            root_cause_hypothesis=finding.description,
            linked_alerts=(alert.alert_id,),
            affected_scope=finding.scope,
            truth_source=truth,
            detail=finding.description,
        )
        rec = transit(rec, IncidentState.TRIAGED, now=now)
        rec = transit(rec, IncidentState.CLASSIFIED, now=now)
        if severity in {SeverityLevel.HIGH, SeverityLevel.CRITICAL}:
            rec = transit(rec, IncidentState.ESCALATED, now=now)
        self.incidents.append(rec)
        return rec

    def by_id(self, incident_id) -> IncidentRecord | None:
        for rec in self.incidents:
            if rec.incident_id == incident_id:
                return rec
        return None

    def replace(self, rec: IncidentRecord) -> None:
        self.incidents = [rec if i.incident_id == rec.incident_id else i for i in self.incidents]

    def open(self) -> tuple[IncidentRecord, ...]:
        return tuple(i for i in self.incidents if i.state not in {IncidentState.CLOSED, IncidentState.TRANSFERRED_TO_PERSISTENCE})

    def suppress(self, rec: IncidentRecord, *, now: datetime, reason: str) -> IncidentRecord:
        nxt = rec.model_copy(update={"suppressed": True, "suppress_reason": reason, "updated_at": now})
        self.replace(nxt)
        return nxt
