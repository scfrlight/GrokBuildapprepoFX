from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.post_trade import PostTradeAlert, TruthSource
from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id
from botmoduleproject1.modules.pm6_post_trade.intake.normalizer import NormalizedObserve
from botmoduleproject1.modules.pm6_post_trade.monitoring.findings import Finding
from botmoduleproject1.modules.pm6_post_trade.surveillance.deduplication import AlertDeduper
from botmoduleproject1.modules.pm6_post_trade.surveillance.detectors import BurstBook, silence_finding, stale_finding


class SurveillanceEngine:
    def __init__(self, config: Pm6PostTradeConfig) -> None:
        self.config = config
        self.bursts = BurstBook(config)
        self.deduper = AlertDeduper(config)
        self.alerts: list[PostTradeAlert] = []
        self.last_event: datetime | None = None

    def to_alert(self, finding: Finding, *, now: datetime, truth: TruthSource, order_id=None) -> PostTradeAlert:
        alert = PostTradeAlert(
            alert_id=new_id(),
            occurred_at=now,
            created_at=now,
            observed_at=now,
            category=finding.category,
            severity=finding.severity,
            detector=finding.detector,
            description=finding.description,
            observed=finding.observed,
            threshold=finding.threshold,
            recommended_action=finding.recommended_action,
            auto_action_status=finding.auto_action,
            truth_source=truth,
            fingerprint=finding.fingerprint or finding.detector,
            scope=finding.scope,
            linked_orders=(order_id,) if order_id else (),
        )
        return self.deduper.apply(alert, now)

    def extra_findings(self, obs: NormalizedObserve, now: datetime) -> list[Finding]:
        out: list[Finding] = []
        exe = obs.execution
        if exe is not None and exe.receipt.accepted:
            burst = self.bursts.note("submit", now)
            if burst:
                out.append(burst)
            if exe.fills:
                fill_burst = self.bursts.note("fill", now)
                if fill_burst:
                    out.append(fill_burst)
        elif exe is not None and not exe.receipt.accepted:
            burst = self.bursts.note("reject", now)
            if burst:
                out.append(burst)
        stale = stale_finding(obs, self.config)
        if stale:
            out.append(stale)
        silent = silence_finding(self.last_event, now, self.config)
        if silent:
            out.append(silent)
        return out
