from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Any

from botmoduleproject1.contracts.v1.post_trade import AuditEvidenceBundle, TruthSource
from botmoduleproject1.modules.pm6_post_trade.config.defaults import POLICY_VERSION
from botmoduleproject1.modules.pm6_post_trade.domain.ids import new_id


class EvidenceRegistry:
    def __init__(self) -> None:
        self.bundles: list[AuditEvidenceBundle] = []
        self.timeline: list[str] = []

    def note(self, line: str) -> None:
        self.timeline.append(line)

    def compile(
        self,
        *,
        now: datetime,
        events: tuple[dict[str, Any], ...] = (),
        incidents=(),
        truth: TruthSource,
        extra: tuple[str, ...] = (),
    ) -> AuditEvidenceBundle:
        timeline = tuple(self.timeline[-40:] + list(extra))
        raw = "|".join(timeline)
        bundle = AuditEvidenceBundle(
            evidence_id=new_id(),
            occurred_at=now,
            events=events,
            incident_ids=tuple(getattr(i, "incident_id", i) for i in incidents),
            timeline=timeline,
            provenance=truth,
            policy_version=POLICY_VERSION,
            fingerprint=sha256(raw.encode()).hexdigest()[:16],
            persistence_handoff="non_durable_before_pm7",
            durable=False,
        )
        self.bundles.append(bundle)
        return bundle
