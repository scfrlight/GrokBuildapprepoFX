from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.post_trade import (
    MonitoringSnapshot,
    MonitoringState,
    TruthSource,
)
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id
from botmoduleproject1.modules.pm6_post_trade.domain.states import worse
from botmoduleproject1.modules.pm6_post_trade.monitoring.freshness import age_seconds, is_stale


def snapshot(
    *,
    now: datetime,
    state: MonitoringState,
    mode: str,
    truth: TruthSource,
    controls: tuple[str, ...],
    open_orders: int,
    fills: int,
    positions: int,
    exposure: Decimal,
    alerts: int,
    incidents: int,
    recon: str,
    last_event: datetime | None,
    ttl: int,
) -> MonitoringSnapshot:
    stale = is_stale(last_event, now, ttl)
    if stale:
        state = worse(state, MonitoringState.WARNING)
    return MonitoringSnapshot(
        monitoring_id=new_id(),
        as_of=now,
        state=state,
        execution_mode=mode,
        truth_source=truth,
        active_controls=controls,
        open_orders=open_orders,
        fills=fills,
        positions=positions,
        exposure=exposure,
        alert_count=alerts,
        incident_count=incidents,
        drift_status="none",
        reconciliation_status=recon,
        broker_truth_available=False,
        operational_status="observe_only",
        freshness_seconds=age_seconds(last_event, now),
        last_event_at=last_event,
        stale=stale,
        durable=False,
    )
