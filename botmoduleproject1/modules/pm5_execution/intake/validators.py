from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import ExecutionMode, ExecutionRejectReason
from botmoduleproject1.contracts.v1.risk import (
    KillSwitchStatus,
    RiskAdmissionDecision,
    RiskPublicationBundle,
    RiskVerdictStatus,
)
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig


def approved_quantity(bundle: RiskPublicationBundle) -> Decimal:
    if bundle.verdict.recommended_volume is not None:
        return bundle.verdict.recommended_volume
    return bundle.sizing.recommended_size


def validate_intake(
    bundle: RiskPublicationBundle | None,
    *,
    now: datetime,
    config: Pm5ExecutionConfig,
    direction: Direction | None,
    quantity: Decimal | None,
    symbol: str | None,
    kill_blocks: bool,
    control_blocks: bool,
    mode: ExecutionMode,
    feature_enabled: bool,
    order_type: str = "market",
    broker_path: bool = False,
) -> list[ExecutionRejectReason]:
    reasons: list[ExecutionRejectReason] = []
    if not feature_enabled or mode is ExecutionMode.DISABLED:
        reasons.append(ExecutionRejectReason.FEATURE_DISABLED)
    if mode is ExecutionMode.LIVE:
        reasons.append(ExecutionRejectReason.LIVE_BLOCKED)
    if bundle is None:
        reasons.append(ExecutionRejectReason.MISSING_AUTHORIZATION)
        return reasons
    if bundle.verdict.correlation_id is None or bundle.idempotency_key in (None, ""):
        reasons.append(ExecutionRejectReason.MISSING_TRACE)
    if getattr(bundle, "schema_version", "v1") != "v1":
        reasons.append(ExecutionRejectReason.SCHEMA_MISMATCH)
    if bundle.verdict.status is not RiskVerdictStatus.ALLOW:
        reasons.append(ExecutionRejectReason.PM4_DENY)
    if bundle.admission.decision in {
        RiskAdmissionDecision.REJECT,
        RiskAdmissionDecision.FREEZE,
        RiskAdmissionDecision.KILL_PROTECTED,
    }:
        reasons.append(ExecutionRejectReason.PM4_DENY)
    if bundle.kill_switch.status in {KillSwitchStatus.TRIPPED, KillSwitchStatus.LATCHED}:
        reasons.append(ExecutionRejectReason.KILL_SWITCH)
    if kill_blocks or control_blocks:
        reasons.append(ExecutionRejectReason.CONTROL_BLOCKED)
    if broker_path or mode not in {ExecutionMode.SIMULATION, ExecutionMode.SHADOW}:
        if not bundle.execution_permitted:
            reasons.append(ExecutionRejectReason.EXECUTION_NOT_PERMITTED)
    if bundle.occurred_at > now:
        reasons.append(ExecutionRejectReason.LOOKAHEAD)
    ttl = timedelta(seconds=config.stale_ttl_seconds)
    if now - bundle.occurred_at > ttl:
        reasons.append(ExecutionRejectReason.STALE_INTENT)
    if bundle.verdict.expires_at is not None and now > bundle.verdict.expires_at:
        reasons.append(ExecutionRejectReason.STALE_INTENT)
    sym = symbol or bundle.symbol
    if sym not in config.symbol_allowlist:
        reasons.append(ExecutionRejectReason.UNSUPPORTED_SYMBOL)
    if direction is None:
        reasons.append(ExecutionRejectReason.UNSUPPORTED_SIDE)
    cap = approved_quantity(bundle)
    qty = quantity if quantity is not None else cap
    if qty is None or qty <= 0:
        reasons.append(ExecutionRejectReason.INVALID_QUANTITY)
    elif qty > cap:
        reasons.append(ExecutionRejectReason.QUANTITY_EXCEEDS_PM4)
    if order_type not in config.allowed_order_types:
        reasons.append(ExecutionRejectReason.INVALID_ORDER_TYPE)
    return list(dict.fromkeys(reasons))
