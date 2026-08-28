from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.post_trade import IncidentType, SeverityLevel
from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig
from botmoduleproject1.modules.pm6_post_trade.intake.normalizer import NormalizedObserve
from botmoduleproject1.modules.pm6_post_trade.monitoring.findings import Finding


class BurstBook:
    def __init__(self, config: Pm6PostTradeConfig) -> None:
        self.config = config
        self.submits: deque[datetime] = deque()
        self.rejects: deque[datetime] = deque()
        self.fills: deque[datetime] = deque()
        self.cancels: deque[datetime] = deque()

    def _prune(self, q: deque, now: datetime) -> None:
        window = timedelta(seconds=self.config.burst_window_seconds)
        while q and now - q[0] > window:
            q.popleft()

    def note(self, kind: str, now: datetime) -> Finding | None:
        mapping = {
            "submit": (self.submits, self.config.submit_burst, "submit_burst"),
            "reject": (self.rejects, self.config.reject_burst, "reject_burst"),
            "fill": (self.fills, self.config.fill_burst, "fill_burst"),
            "cancel": (self.cancels, self.config.cancel_burst, "cancel_storm"),
        }
        q, limit, detector = mapping[kind]
        self._prune(q, now)
        q.append(now)
        if len(q) > limit:
            return Finding(
                detector=detector,
                category="execution",
                severity=SeverityLevel.HIGH,
                description=f"{detector} exceeded {limit} in window",
                recommended_action="throttle",
                incident_type=IncidentType.MONITORING_ALERT_BURST,
                observed={"count": len(q)},
                threshold={"limit": limit},
                fingerprint=f"{detector}|window",
            )
        return None


def silence_finding(last_event: datetime | None, now: datetime, config: Pm6PostTradeConfig) -> Finding | None:
    if last_event is None:
        return None
    gap = now - last_event
    if gap > timedelta(seconds=config.silence_seconds):
        return Finding(
            detector="monitoring_silence",
            category="monitoring",
            severity=SeverityLevel.MEDIUM,
            description="monitoring feed silent beyond threshold",
            recommended_action="degrade",
            incident_type=IncidentType.STALE_MONITORING_DATA,
            observed={"gap_s": int(gap.total_seconds())},
            threshold={"silence_s": config.silence_seconds},
            fingerprint="silence",
        )
    return None


def stale_finding(obs: NormalizedObserve, config: Pm6PostTradeConfig) -> Finding | None:
    stamp = None
    if obs.execution is not None:
        stamp = obs.execution.occurred_at
    elif obs.risk is not None:
        stamp = obs.risk.occurred_at
    if stamp is None:
        return None
    gap = obs.now - stamp
    if gap > timedelta(seconds=config.freshness_ttl_seconds):
        return Finding(
            detector="stale_event",
            category="monitoring",
            severity=SeverityLevel.MEDIUM,
            description="event older than freshness TTL",
            recommended_action="degrade",
            incident_type=IncidentType.STALE_MONITORING_DATA,
            observed={"age_s": int(gap.total_seconds())},
            fingerprint="stale",
        )
    return None
