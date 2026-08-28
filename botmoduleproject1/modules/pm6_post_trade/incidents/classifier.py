from __future__ import annotations

from botmoduleproject1.contracts.v1.post_trade import (
    IncidentCategory,
    IncidentType,
    SeverityLevel,
)
from botmoduleproject1.modules.pm6_post_trade.monitoring.findings import Finding

_TYPE_TO_CATEGORY = {
    IncidentType.POST_TRADE_CONTROL_BREACH: IncidentCategory.RISK_CONTROL,
    IncidentType.MONITORING_ALERT_BURST: IncidentCategory.MONITORING,
    IncidentType.EXECUTION_ANOMALY: IncidentCategory.EXECUTION,
    IncidentType.RECONCILIATION_FOLLOWUP_REQUIRED: IncidentCategory.RECONCILIATION,
    IncidentType.KILL_STATE_BREACH: IncidentCategory.RISK_CONTROL,
    IncidentType.ORDERLY_WITHDRAWAL_REQUIRED: IncidentCategory.GOVERNANCE,
    IncidentType.MANUAL_OVERRIDE_INCIDENT: IncidentCategory.OPERATOR,
    IncidentType.AUDIT_EVIDENCE_GAP: IncidentCategory.GOVERNANCE,
    IncidentType.VALIDATION_GAP: IncidentCategory.GOVERNANCE,
    IncidentType.UNEXPECTED_TRADING_CONTINUATION: IncidentCategory.EXECUTION,
    IncidentType.STALE_MONITORING_DATA: IncidentCategory.MONITORING,
    IncidentType.TRUTH_PROVENANCE_CONFLICT: IncidentCategory.DATA_QUALITY,
    IncidentType.REPEATED_EXECUTION_ANOMALY: IncidentCategory.EXECUTION,
    IncidentType.CONTROL_STATE_INCONSISTENCY: IncidentCategory.RISK_CONTROL,
}


def classify(finding: Finding) -> tuple[IncidentType, IncidentCategory, SeverityLevel]:
    itype = finding.incident_type or IncidentType.EXECUTION_ANOMALY
    return itype, _TYPE_TO_CATEGORY.get(itype, IncidentCategory.MONITORING), finding.severity
