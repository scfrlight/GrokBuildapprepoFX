"""Ghost / abstain analytics. Tracks what did not promote."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import (
    PublicationBundle,
    QualificationStateName,
    QualityTier,
    RankedCandidate,
)


def ghost_records(
    ranked: tuple[RankedCandidate, ...],
    bundle: PublicationBundle,
) -> tuple[dict[str, object], ...]:
    short_ids = {c.candidate_id for c in bundle.shortlist}
    watch_ids = {c.candidate_id for c in bundle.watchlist}
    out: list[dict[str, object]] = []
    for item in ranked:
        kind = None
        if item.suppression is not None or item.state.state is QualificationStateName.SUPPRESSED:
            kind = "suppressed"
        elif item.state.state is QualificationStateName.STALE:
            kind = "expired_before_confirmation"
        elif item.candidate_id in watch_ids and item.candidate_id not in short_ids:
            kind = "watchlisted_not_promoted"
        elif item.scorecard.quality_tier is QualityTier.SUPPRESS:
            kind = "rejected"
        if kind is None:
            continue
        out.append(
            {
                "symbol": item.symbol,
                "kind": kind,
                "score": item.scorecard.final_confluence_score,
                "state": item.state.state.value,
                "ghost_tracking_eligibility": True
                if item.suppression is None
                else item.suppression.ghost_tracking_eligibility,
            }
        )
    return tuple(out)
