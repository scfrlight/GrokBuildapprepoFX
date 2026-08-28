"""Suppression policy knobs. Fail closed toward suppress."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import QualityTier, RankedCandidate
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config


def must_suppress(candidate: RankedCandidate, config: Pm2Config) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.scorecard.vetoes:
        reasons.extend(f"veto:{v}" for v in candidate.scorecard.vetoes)
    if candidate.scorecard.quality_tier is QualityTier.SUPPRESS:
        reasons.append("band:suppress")
    if candidate.scorecard.confidence_score < config.thresholds.min_confidence:
        reasons.append("confidence:low")
    return tuple(reasons)
