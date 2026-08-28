from __future__ import annotations

from collections import Counter
from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import (
    GovernanceReviewPacket,
    GovernanceReviewState,
    IncidentRecord,
    PostTradeAlert,
    ValidationReviewPacket,
)
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id


def governance_packet(
    *,
    now: datetime,
    alerts: tuple[PostTradeAlert, ...],
    incidents: tuple[IncidentRecord, ...],
) -> GovernanceReviewPacket:
    return GovernanceReviewPacket(
        packet_id=new_id(),
        generated_at=now,
        period="session",
        kind="daily",
        incident_trends=dict(Counter(i.incident_type.value for i in incidents)),
        alert_trends=dict(Counter(a.detector for a in alerts)),
        unresolved=sum(1 for i in incidents if i.state.value not in {"closed", "transferred_to_persistence"}),
        control_trigger_counts=dict(Counter(a.detector for a in alerts if a.category in {"risk/control", "execution"})),
        false_positive_observations="insufficient_data",
        recommendations=("retain_simulation_truth_label", "do_not_treat_degraded_recon_as_pass"),
        state=GovernanceReviewState.SCHEDULED,
    )


def validation_packet(*, now: datetime, alert_count: int, incident_count: int) -> ValidationReviewPacket:
    return ValidationReviewPacket(
        packet_id=new_id(),
        generated_at=now,
        rule_performance={"alerts": alert_count, "incidents": incident_count},
        alert_precision="insufficient_data",
        false_positive="insufficient_data",
        false_negative="insufficient_data",
        missed_event="insufficient_data",
        control_calibration="not_available",
        sample_size=alert_count,
        review_state=GovernanceReviewState.SCHEDULED,
    )
