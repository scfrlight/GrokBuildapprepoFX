"""Schema, freshness, traceability, and semantic consistency checks."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, QualificationStateName
from botmoduleproject1.contracts.v1.risk import RiskRejectionReason
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


def _aware(value: datetime, name: str) -> datetime:
    return ensure_aware_utc(value, name)


def validate_intake(
    request: RiskIntakeRequest,
    config: Pm4RiskGateConfig,
    now: datetime,
) -> list[RiskRejectionReason]:
    reasons: list[RiskRejectionReason] = []
    now = _aware(now, "now")
    as_of = _aware(request.as_of, "as_of")
    ttl = timedelta(seconds=config.stale_ttl_seconds)

    if as_of > now:
        reasons.append(RiskRejectionReason.LOOKAHEAD)
    intent = request.intent
    try:
        occurred = _aware(intent.occurred_at, "occurred_at")
    except (TypeError, ValueError):
        return [RiskRejectionReason.MALFORMED]
    if occurred > now:
        reasons.append(RiskRejectionReason.LOOKAHEAD)
    if now - occurred > ttl:
        reasons.append(RiskRejectionReason.STALE_DATA)
    if intent.signal_expiry is not None:
        expiry = _aware(intent.signal_expiry, "signal_expiry")
        if now > expiry:
            reasons.append(RiskRejectionReason.STALE_DATA)
    if intent.direction is Direction.FLAT:
        reasons.append(RiskRejectionReason.INVALID_INTENT)
    if not intent.symbol.strip():
        reasons.append(RiskRejectionReason.INVALID_INTENT)

    candidate = request.candidate
    if candidate is None:
        reasons.append(RiskRejectionReason.MISSING_CANDIDATE)
    else:
        cand_as_of = _aware(candidate.as_of, "candidate.as_of")
        if cand_as_of > now:
            reasons.append(RiskRejectionReason.LOOKAHEAD)
        if now - cand_as_of > ttl:
            reasons.append(RiskRejectionReason.STALE_DATA)
        if candidate.symbol != intent.symbol:
            reasons.append(RiskRejectionReason.SYMBOL_MISMATCH)
        if (
            intent.source_candidate_id is not None
            and intent.source_candidate_id != candidate.candidate_id
        ):
            reasons.append(RiskRejectionReason.MALFORMED)
        if not candidate.handoff_eligibility:
            reasons.append(RiskRejectionReason.HANDOFF_INELIGIBLE)
        if candidate.state.state in {
            QualificationStateName.STALE,
            QualificationStateName.SUPPRESSED,
            QualificationStateName.INVALIDATED,
            QualificationStateName.COOLDOWN,
        }:
            reasons.append(RiskRejectionReason.HANDOFF_INELIGIBLE)
        if candidate.context.data_quality in {
            DataQualityStatus.STALE,
            DataQualityStatus.MALFORMED,
            DataQualityStatus.INCOMPLETE,
        }:
            reasons.append(RiskRejectionReason.STALE_DATA)
        if candidate.timing_valid_until is not None:
            until = _aware(candidate.timing_valid_until, "timing_valid_until")
            if now > until:
                reasons.append(RiskRejectionReason.STALE_DATA)

    forecast = request.forecast
    if forecast is None:
        reasons.append(RiskRejectionReason.MISSING_FORECAST)
    else:
        fx_at = _aware(forecast.occurred_at, "forecast.occurred_at")
        if fx_at > now:
            reasons.append(RiskRejectionReason.LOOKAHEAD)
        if now - fx_at > ttl:
            reasons.append(RiskRejectionReason.STALE_DATA)
        if forecast.symbol != intent.symbol:
            reasons.append(RiskRejectionReason.SYMBOL_MISMATCH)
        if forecast.intent_id != intent.intent_id:
            reasons.append(RiskRejectionReason.MALFORMED)
        if not forecast.diagnostics:
            reasons.append(RiskRejectionReason.FORECAST_INVALID)
        else:
            if forecast.diagnostics.get("lookahead") is True:
                reasons.append(RiskRejectionReason.LOOKAHEAD)
            if forecast.diagnostics.get("forming_bar") is True:
                reasons.append(RiskRejectionReason.FORECAST_INVALID)
            if forecast.diagnostics.get("valid") is False:
                reasons.append(RiskRejectionReason.FORECAST_INVALID)
        samples = forecast.sample_size
        if samples is None or samples < config.min_forecast_samples:
            reasons.append(RiskRejectionReason.FORECAST_INVALID)

    stop = _stop_distance(request)
    if stop is None:
        reasons.append(RiskRejectionReason.STOP_MISSING)
    elif stop < config.min_stop_distance or stop > config.max_stop_distance:
        reasons.append(RiskRejectionReason.INVALID_INTENT)

    # unique, preserve order
    seen: set[RiskRejectionReason] = set()
    ordered: list[RiskRejectionReason] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    return ordered


def _stop_distance(request: RiskIntakeRequest) -> Decimal | None:
    intent = request.intent
    plan = intent.exit_plan
    entry = intent.entry_price
    if entry is None and intent.entry_zone_low is not None and intent.entry_zone_high is not None:
        entry = (intent.entry_zone_low + intent.entry_zone_high) / Decimal("2")
    if entry is None and request.mid_price is not None:
        entry = request.mid_price
    if plan is None or entry is None:
        return None
    stop = plan.stop_price if plan.stop_price is not None else plan.stop_loss
    if stop is None:
        return None
    distance = abs(entry - stop)
    if distance <= 0:
        return None
    return distance


def reference_price(request: RiskIntakeRequest) -> Decimal | None:
    intent = request.intent
    if intent.entry_price is not None:
        return intent.entry_price
    if intent.entry_zone_low is not None and intent.entry_zone_high is not None:
        return (intent.entry_zone_low + intent.entry_zone_high) / Decimal("2")
    return request.mid_price


def interval_width(request: RiskIntakeRequest) -> Decimal | None:
    forecast = request.forecast
    if forecast is None:
        return None
    q = forecast.quantiles
    return q.q95 - q.q05
