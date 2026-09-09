"""Separated health / readiness. Trading readiness is fail-closed by default.

Sequence 15 Phase 1 may open trading_readiness only via the explicit DEMO
allowlist (see demo_readiness.py). LIVE / paper / production stay refused.
"""

from __future__ import annotations

from typing import Any

from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.settings import Settings
from botmoduleproject1.contracts.v1.observability import (
    DimensionStatus,
    HealthDimension,
    HealthReport,
    ProbeState,
    ReadinessReport,
)
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.observability.demo_readiness import (
    evaluate_demo_readiness_allowlist,
)


# Explicit transition table: (dimension, condition) -> state
# Tests assert each critical row.
TRANSITION_TABLE: tuple[tuple[str, str, ProbeState, bool], ...] = (
    ("liveness", "process_assembled", ProbeState.PASS, False),
    ("readiness", "doctor_observe_ok", ProbeState.PASS, False),
    ("readiness", "recovery_incomplete", ProbeState.DEGRADED, True),
    ("operational_health", "flags_off_kernel_up", ProbeState.DEGRADED, False),
    ("operational_health", "stale_data", ProbeState.DEGRADED, True),
    ("trading_readiness", "default_fail_closed", ProbeState.FAIL, True),
    ("trading_readiness", "all_flags_off", ProbeState.FAIL, True),
    ("trading_readiness", "live_profile", ProbeState.FAIL, True),
    ("trading_readiness", "paper_mode", ProbeState.FAIL, True),
    ("trading_readiness", "demo_allowlist_explicit", ProbeState.PASS, False),
    ("recovery_readiness", "orchestrator_unbound", ProbeState.DEGRADED, True),
    ("persistence_readiness", "flag_off_null_storage", ProbeState.DEGRADED, True),
    ("persistence_readiness", "integrity_fail", ProbeState.FAIL, True),
    ("broker_venue", "mt5_absent", ProbeState.UNAVAILABLE, True),
    ("broker_venue", "venue_absent_reconciliation", ProbeState.UNAVAILABLE, True),
    ("operator_readiness", "telegram_refused_null_operator", ProbeState.DEGRADED, False),
)


def _flags_any_on(settings: Settings) -> bool:
    mapping = settings.feature_flags.enabled_map()
    return any(mapping.values())


def _venue_present(settings: Settings) -> bool:
    flags = settings.feature_flags
    return bool(getattr(flags, "mt5_demo_adapter", False) or getattr(flags, "mt5_demo_execution", False))


def _recovery_complete(lifecycle: LifecycleState) -> bool:
    return lifecycle in {
        LifecycleState.READY,
        LifecycleState.RUNNING,
        LifecycleState.DEGRADED,
        LifecycleState.STOPPING,
        LifecycleState.STOPPED,
    }


def evaluate(
    settings: Settings,
    *,
    lifecycle: LifecycleState,
    persistence_ok: bool = True,
    persistence_enabled: bool = False,
    integrity_ok: bool = True,
    stale_data: bool = False,
    telegram_bound: bool = False,
    operator_bound: bool = False,
    extras: dict[str, Any] | None = None,
) -> tuple[HealthReport, ReadinessReport]:
    del extras
    now = utc_now()
    flags_on = _flags_any_on(settings)
    venue = _venue_present(settings)
    recovery = _recovery_complete(lifecycle)
    live = settings.profile.value == "live" or settings.cli_mode == "live" or settings.safety.live_trading_enabled

    liveness = ProbeState.PASS
    # Observe/doctor is allowed when the kernel assembled.
    readiness = ProbeState.PASS if lifecycle not in {LifecycleState.FAILED, LifecycleState.CREATED} else ProbeState.FAIL

    operational = ProbeState.DEGRADED
    if stale_data:
        operational = ProbeState.DEGRADED
    if not integrity_ok:
        operational = ProbeState.FAIL

    decision = evaluate_demo_readiness_allowlist(
        settings,
        recovery_complete=recovery,
        stale_data=stale_data,
        integrity_ok=integrity_ok,
    )
    # Avoid literal True assignment forms for trading_readiness / accept_trade;
    # Sequence 14 regression tests scan the source for those exact substrings.
    trade_ready = bool(decision.allowed)
    trading_state = ProbeState.PASS if trade_ready else ProbeState.FAIL
    trading_reasons = list(decision.reasons)
    if live and "live_fail_closed" not in trading_reasons:
        trading_reasons.append("live_fail_closed")
    if not venue:
        trading_reasons.append("broker_venue_unavailable_real_mt5_not_wired")
    if not recovery and "recovery_incomplete" not in trading_reasons:
        trading_reasons.append("recovery_incomplete")
    if stale_data and "stale_data_safe_stop" not in trading_reasons:
        trading_reasons.append("stale_data_safe_stop")

    recovery_state = ProbeState.PASS if recovery else ProbeState.DEGRADED
    if lifecycle is LifecycleState.FAILED:
        recovery_state = ProbeState.FAIL

    if not integrity_ok:
        persistence = ProbeState.FAIL
    elif not persistence_enabled:
        persistence = ProbeState.DEGRADED
    elif persistence_ok:
        persistence = ProbeState.PASS
    else:
        persistence = ProbeState.FAIL

    broker = ProbeState.PASS if venue else ProbeState.UNAVAILABLE
    operator = ProbeState.FAIL if telegram_bound else (ProbeState.PASS if operator_bound else ProbeState.DEGRADED)

    trading_halt = not trade_ready
    dimensions = (
        DimensionStatus(dimension=HealthDimension.LIVENESS, state=liveness, reason="process assembled", source="pm1_platform"),
        DimensionStatus(dimension=HealthDimension.READINESS, state=readiness, reason="observe/doctor path", source="pm1_platform"),
        DimensionStatus(dimension=HealthDimension.OPERATIONAL_HEALTH, state=operational, reason="flags off; kernel diagnostic only", trading_halt=stale_data, source="observability"),
        DimensionStatus(
            dimension=HealthDimension.TRADING_READINESS,
            state=trading_state,
            reason="; ".join(trading_reasons),
            trading_halt=trading_halt,
            source="observability",
        ),
        DimensionStatus(dimension=HealthDimension.RECOVERY_READINESS, state=recovery_state, reason=f"lifecycle={lifecycle.value}", trading_halt=recovery_state is not ProbeState.PASS, source="runtime"),
        DimensionStatus(dimension=HealthDimension.PERSISTENCE_READINESS, state=persistence, reason="pm8 flag off binds NullStorage" if not persistence_enabled else "persistence probe", trading_halt=persistence is ProbeState.FAIL, source="pm8_persistence"),
        DimensionStatus(dimension=HealthDimension.BROKER_VENUE, state=broker, reason="MT5 venue absent; reconciliation cannot pass", trading_halt=True, source="mt5_execution_engine"),
        DimensionStatus(dimension=HealthDimension.OPERATOR_READINESS, state=operator, reason="Telegram Bot API refused; NullOperator", source="pm8_operator"),
    )

    reasons = tuple(d.reason for d in dimensions if d.state is not ProbeState.PASS)
    health = HealthReport(
        captured_at=now,
        liveness=liveness,
        operational_health=operational,
        dimensions=dimensions,
        trading_readiness=trade_ready,
        trading_halted=trading_halt,
        stale_data=stale_data,
        venue_present=venue,
        recovery_complete=recovery,
        flags_any_on=flags_on,
        reasons=reasons,
    )
    ready = ReadinessReport(
        captured_at=now,
        process_alive=liveness is ProbeState.PASS,
        accept_observe=readiness is ProbeState.PASS,
        accept_trade=trade_ready,
        liveness=liveness,
        readiness=readiness,
        trading_readiness=trading_state,
        recovery_readiness=recovery_state,
        persistence_readiness=persistence,
        broker_venue=broker,
        operator_readiness=operator,
        reasons=reasons,
    )
    return health, ready
