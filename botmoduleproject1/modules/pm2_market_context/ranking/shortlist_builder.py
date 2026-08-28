"""Shortlist / watchlist split from a ranked set."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import (
    QualificationStateName,
    QualityTier,
    RankedCandidate,
)
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config

_DEAD = {
    QualificationStateName.SUPPRESSED,
    QualificationStateName.INVALIDATED,
    QualificationStateName.STALE,
}


def build_shortlist(
    ranked: tuple[RankedCandidate, ...],
    config: Pm2Config,
) -> tuple[RankedCandidate, ...]:
    picked: list[RankedCandidate] = []
    for item in ranked:
        if item.state.state in _DEAD:
            continue
        if item.scorecard.quality_tier in {QualityTier.ELIGIBLE, QualityTier.HIGH, QualityTier.TOP}:
            picked.append(item)
        if len(picked) >= config.thresholds.shortlist_size:
            break
    return tuple(picked)


def build_watchlist(
    ranked: tuple[RankedCandidate, ...],
    shortlist: tuple[RankedCandidate, ...],
    config: Pm2Config,
) -> tuple[RankedCandidate, ...]:
    short_ids = {c.candidate_id for c in shortlist}
    picked: list[RankedCandidate] = []
    for item in ranked:
        if item.candidate_id in short_ids:
            continue
        if item.state.state in _DEAD:
            continue
        if item.scorecard.quality_tier is QualityTier.WATCH or item.state.state is QualificationStateName.FORMING:
            picked.append(item)
        if len(picked) >= config.thresholds.watchlist_size:
            break
    return tuple(picked)
