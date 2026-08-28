"""Downstream-safe handoff. Never an order, size, or broker action."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import QualificationStateName, QualityTier, RankedCandidate
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config
from botmoduleproject1.modules.pm2_market_context.domain.enums import OperatingMode

_HANDOFF_STATES = {QualificationStateName.QUALIFIED, QualificationStateName.CONFIRMED}
_HANDOFF_TIERS = {QualityTier.ELIGIBLE, QualityTier.HIGH, QualityTier.TOP}


def eligible_for_handoff(candidate: RankedCandidate, config: Pm2Config) -> bool:
    if config.operating_mode is OperatingMode.SHADOW:
        return False
    if candidate.scorecard.vetoes:
        return False
    if candidate.suppression is not None:
        return False
    if candidate.state.state not in _HANDOFF_STATES:
        return False
    if candidate.scorecard.quality_tier not in _HANDOFF_TIERS:
        return False
    if candidate.scorecard.confidence_score < config.thresholds.min_confidence:
        return False
    return True


def stamp_handoff(
    candidates: tuple[RankedCandidate, ...],
    config: Pm2Config,
) -> tuple[RankedCandidate, ...]:
    out: list[RankedCandidate] = []
    for item in candidates:
        flag = eligible_for_handoff(item, config)
        if flag is item.handoff_eligibility:
            out.append(item)
        else:
            out.append(item.model_copy(update={"handoff_eligibility": flag}))
    return tuple(out)
