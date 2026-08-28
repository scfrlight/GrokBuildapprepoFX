from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import ExecutionLifecycleState, ReconciliationOutcome
from botmoduleproject1.contracts.v1.post_trade import IncidentType, SeverityLevel
from botmoduleproject1.modules.pm6_post_trade.intake.normalizer import NormalizedObserve
from botmoduleproject1.modules.pm6_post_trade.monitoring.findings import Finding


def _fp(*parts: object) -> str:
    return "|".join(str(p) for p in parts)


def evaluate_controls(obs: NormalizedObserve, *, withdrawal_active: bool) -> list[Finding]:
    findings: list[Finding] = []
    exe = obs.execution
    if exe is None:
        return findings
    order = exe.order
    ticket = order.broker_ticket if order else None

    if ticket and str(ticket).startswith("SIM-") and exe.reconciliation and exe.reconciliation.broker_truth_available:
        findings.append(
            Finding(
                detector="sim_as_broker",
                category="data-quality",
                severity=SeverityLevel.CRITICAL,
                description="SIM-* ticket presented with broker_truth_available",
                recommended_action="quarantine_and_review",
                incident_type=IncidentType.TRUTH_PROVENANCE_CONFLICT,
                fingerprint=_fp("sim_as_broker", ticket),
            )
        )

    if obs.approved is not None and obs.filled is not None and obs.filled > obs.approved:
        findings.append(
            Finding(
                detector="quantity_drift",
                category="execution",
                severity=SeverityLevel.HIGH,
                description="filled quantity exceeds PM4/PM5 approved quantity",
                recommended_action="contain_and_review",
                incident_type=IncidentType.POST_TRADE_CONTROL_BREACH,
                observed={"approved": str(obs.approved), "filled": str(obs.filled)},
                fingerprint=_fp("quantity_drift", order.order_id if order else "none"),
            )
        )

    accepted = bool(exe.receipt.accepted)
    inactive = {
        ExecutionLifecycleState.REJECTED,
        ExecutionLifecycleState.CANCELLED,
        ExecutionLifecycleState.EXPIRED,
        ExecutionLifecycleState.BLOCKED,
    }
    working = order is not None and order.state not in inactive
    if obs.kill and accepted and working:
        findings.append(
            Finding(
                detector="execution_after_kill",
                category="risk/control",
                severity=SeverityLevel.CRITICAL,
                description="execution activity after kill-switch latch",
                recommended_action="emergency_containment",
                incident_type=IncidentType.KILL_STATE_BREACH,
                fingerprint=_fp("kill_breach", order.order_id if order else "none"),
            )
        )
        findings.append(
            Finding(
                detector="unexpected_continuation",
                category="execution",
                severity=SeverityLevel.CRITICAL,
                description="trading continuation while kill is latched",
                recommended_action="orderly_withdrawal",
                incident_type=IncidentType.UNEXPECTED_TRADING_CONTINUATION,
                fingerprint=_fp("continuation", order.order_id if order else "none"),
            )
        )

    if obs.freeze and accepted and working and not obs.kill:
        findings.append(
            Finding(
                detector="execution_after_freeze",
                category="risk/control",
                severity=SeverityLevel.HIGH,
                description="execution activity after freeze/halt admission",
                recommended_action="freeze_and_review",
                incident_type=IncidentType.CONTROL_STATE_INCONSISTENCY,
                fingerprint=_fp("freeze_breach", order.order_id if order else "none"),
            )
        )

    recon = exe.reconciliation
    if recon is not None and recon.outcome is ReconciliationOutcome.CRITICAL:
        findings.append(
            Finding(
                detector="recon_critical",
                category="reconciliation",
                severity=SeverityLevel.CRITICAL,
                description="critical reconciliation mismatch",
                recommended_action="block_new_and_recover",
                incident_type=IncidentType.RECONCILIATION_FOLLOWUP_REQUIRED,
                fingerprint=_fp("recon_critical", recon.record_id),
            )
        )
    elif recon is not None and recon.outcome is ReconciliationOutcome.MISMATCH:
        findings.append(
            Finding(
                detector="recon_mismatch",
                category="reconciliation",
                severity=SeverityLevel.HIGH,
                description="local versus claimed broker state mismatch",
                recommended_action="manual_review",
                incident_type=IncidentType.RECONCILIATION_FOLLOWUP_REQUIRED,
                fingerprint=_fp("recon_mismatch", recon.record_id),
            )
        )

    if order is not None and order.filled_quantity > 0 and recon is not None and recon.broker_position_count == 0:
        if recon.broker_truth_available:
            findings.append(
                Finding(
                    detector="unexpected_position",
                    category="execution",
                    severity=SeverityLevel.HIGH,
                    description="local fill with no broker position",
                    recommended_action="reconcile",
                    incident_type=IncidentType.EXECUTION_ANOMALY,
                    fingerprint=_fp("unexpected_position", order.order_id),
                )
            )

    if withdrawal_active and accepted and working:
        findings.append(
            Finding(
                detector="activity_during_withdrawal",
                category="governance",
                severity=SeverityLevel.HIGH,
                description="execution after orderly withdrawal initiation",
                recommended_action="halt_and_review",
                incident_type=IncidentType.UNEXPECTED_TRADING_CONTINUATION,
                fingerprint=_fp("withdrawal_activity", order.order_id if order else "none"),
            )
        )

    if accepted and order is not None and not exe.lifecycle:
        findings.append(
            Finding(
                detector="missing_lifecycle",
                category="monitoring",
                severity=SeverityLevel.MEDIUM,
                description="accepted receipt without lifecycle events",
                recommended_action="review_feed",
                incident_type=IncidentType.AUDIT_EVIDENCE_GAP,
                fingerprint=_fp("missing_lifecycle", order.order_id),
            )
        )

    return findings
