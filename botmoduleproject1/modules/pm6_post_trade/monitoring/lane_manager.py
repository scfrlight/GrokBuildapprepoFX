from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import (
    IncidentRecord,
    LaneKind,
    LaneSummary,
    PostTradeAlert,
    SeverityLevel,
)
from botmoduleproject1.modules.pm6_post_trade.incidents.severity import worse as worse_sev


def build_lanes(
    *,
    now: datetime,
    alerts: tuple[PostTradeAlert, ...],
    incidents: tuple[IncidentRecord, ...],
    mode: str,
    recon: str,
    truth: str,
    accepted: bool,
    kill: bool,
) -> tuple[LaneSummary, LaneSummary]:
    open_inc = tuple(i for i in incidents if i.state.value not in {"closed", "transferred_to_persistence"})
    control_alerts = tuple(a for a in alerts if a.category in {"risk/control", "reconciliation", "data-quality"})
    op_priority = SeverityLevel.INFO
    ctl_priority = SeverityLevel.INFO
    for a in alerts:
        if a.suppressed:
            continue
        op_priority = worse_sev(op_priority, a.severity)
    for a in control_alerts:
        if a.suppressed:
            continue
        ctl_priority = worse_sev(ctl_priority, a.severity)
    if kill:
        ctl_priority = worse_sev(ctl_priority, SeverityLevel.CRITICAL)
    op_items = [
        f"mode={mode}",
        f"accepted={accepted}",
        f"open_incidents={len(open_inc)}",
        f"truth={truth}",
    ]
    ctl_items = [
        f"recon={recon}",
        f"kill={kill}",
        f"control_alerts={len(control_alerts)}",
        f"truth={truth}",
    ]
    operator = LaneSummary(
        lane=LaneKind.OPERATOR,
        as_of=now,
        priority=op_priority,
        headline="operator working picture",
        items=tuple(op_items),
        recommended_action="observe" if op_priority in {SeverityLevel.INFO, SeverityLevel.LOW} else "respond",
        incident_count=len(open_inc),
        alert_count=len(alerts),
    )
    control = LaneSummary(
        lane=LaneKind.CONTROL,
        as_of=now,
        priority=ctl_priority,
        headline="independent risk/control picture",
        items=tuple(ctl_items),
        recommended_action="observe" if ctl_priority in {SeverityLevel.INFO, SeverityLevel.LOW} else "contain",
        incident_count=len(open_inc),
        alert_count=len(control_alerts),
    )
    return operator, control
