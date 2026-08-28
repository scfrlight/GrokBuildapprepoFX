from __future__ import annotations

from datetime import datetime, timedelta, timezone

from botmoduleproject1.contracts.v1.persistence import IngestDisposition, IngestResult, LedgerEvent, PersistenceTruthSource
from botmoduleproject1.modules.pm7_persistence.domain.policies import ALLOWED_SOURCE_MODULES


FUTURE_SKEW = timedelta(seconds=5)


def validate_event(event: LedgerEvent, *, now: datetime, feature_enabled: bool) -> IngestResult | None:
    if not feature_enabled:
        return IngestResult(disposition=IngestDisposition.FEATURE_DISABLED, reasons=("feature_disabled",))
    reasons: list[str] = []
    if event.source_module not in ALLOWED_SOURCE_MODULES:
        reasons.append("unknown_source_module")
    if event.event_timestamp.tzinfo is None:
        reasons.append("naive_timestamp")
    if event.event_timestamp > now + FUTURE_SKEW:
        reasons.append("future_dated")
    if event.trace_id is None:
        reasons.append("missing_trace")
    ticket = event.ticket or ""
    if ticket.startswith("SIM-") and event.truth_source is PersistenceTruthSource.PM5_BROKER:
        reasons.append("sim_labelled_broker_truth")
    if event.event_payload.get("mt5_used") is True:
        reasons.append("mt5_used_forbidden")
    if event.event_payload.get("broker_side_effect") is True:
        reasons.append("broker_side_effect_forbidden")
    if reasons:
        disp = IngestDisposition.REJECTED
        if "unknown_source_module" in reasons or "future_dated" in reasons:
            disp = IngestDisposition.QUARANTINED
        if "sim_labelled_broker_truth" in reasons:
            disp = IngestDisposition.REJECTED
        return IngestResult(
            disposition=disp,
            event_id=event.event_id,
            reasons=tuple(reasons),
            truth_source=event.truth_source,
        )
    return None
