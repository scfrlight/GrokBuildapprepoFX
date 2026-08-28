from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.execution import ExecutionMode, ExecutionPublicationBundle
from botmoduleproject1.contracts.v1.post_trade import IntakeDisposition, IntakeRecord
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig


def validate_observe(
    execution: ExecutionPublicationBundle | None,
    risk: RiskPublicationBundle | None,
    *,
    now: datetime,
    config: Pm6PostTradeConfig,
    feature_enabled: bool,
) -> IntakeRecord:
    reasons: list[str] = []
    disposition = IntakeDisposition.ACCEPTED
    if not feature_enabled:
        return IntakeRecord(
            disposition=IntakeDisposition.REJECTED,
            reasons=("feature_disabled",),
            detail="enable_pm6_post_trade is off",
            occurred_at=now,
        )
    if execution is None and risk is None:
        return IntakeRecord(
            disposition=IntakeDisposition.QUARANTINED,
            reasons=("missing_source",),
            detail="neither PM5 nor PM4 payload provided",
            occurred_at=now,
        )
    stamp = None
    trace = None
    event_id = None
    if execution is not None:
        stamp = execution.occurred_at
        event_id = execution.bundle_id
        if execution.order is not None:
            trace = execution.order.correlation_id
        elif execution.receipt.order_id is not None:
            trace = execution.receipt.order_id
        else:
            reasons.append("missing_trace")
        if execution.schema_version != "v1":
            reasons.append("unsupported_version")
        if not execution.execution_mode:
            reasons.append("missing_execution_mode")
        ticket = execution.order.broker_ticket if execution.order else None
        if ticket and str(ticket).startswith("SIM-"):
            recon = execution.reconciliation
            if recon is not None and recon.broker_truth_available:
                reasons.append("sim_labelled_broker_truth")
            if execution.receipt.simulation is False:
                reasons.append("sim_labelled_broker_truth")
        if execution.mt5_used or execution.broker_side_effect:
            reasons.append("broker_side_effect_forbidden")
        if execution.execution_mode is ExecutionMode.LIVE:
            reasons.append("live_blocked")
        if execution.order is not None and execution.order.correlation_id is None:
            reasons.append("missing_trace")
    if risk is not None:
        stamp = stamp or risk.occurred_at
        event_id = event_id or risk.bundle_id
        trace = trace or risk.correlation_id
        if risk.schema_version != "v1":
            reasons.append("unsupported_version")
        if not risk.idempotency_key:
            reasons.append("missing_trace")
    if stamp is not None:
        if stamp > now:
            reasons.append("future_dated")
            disposition = IntakeDisposition.REJECTED
        elif now - stamp > timedelta(seconds=config.stale_ttl_seconds):
            reasons.append("stale")
            if disposition is IntakeDisposition.ACCEPTED:
                disposition = IntakeDisposition.QUARANTINED
    if "sim_labelled_broker_truth" in reasons or "broker_side_effect_forbidden" in reasons:
        disposition = IntakeDisposition.REJECTED
    elif "unsupported_version" in reasons or "live_blocked" in reasons:
        disposition = IntakeDisposition.REJECTED
    elif "missing_trace" in reasons or "missing_execution_mode" in reasons:
        if disposition is IntakeDisposition.ACCEPTED:
            disposition = IntakeDisposition.REJECTED
    if disposition is IntakeDisposition.ACCEPTED and execution is not None:
        recon = execution.reconciliation
        if recon is None or not recon.broker_truth_available:
            disposition = IntakeDisposition.DEGRADED
            if "broker_truth_unavailable" not in reasons:
                reasons.append("broker_truth_unavailable")
    reasons = list(dict.fromkeys(reasons))
    return IntakeRecord(
        disposition=disposition,
        reasons=tuple(reasons),
        detail=",".join(reasons) if reasons else "accepted",
        event_id=event_id,
        trace_id=trace if hasattr(trace, "hex") else None,
        occurred_at=now,
    )
