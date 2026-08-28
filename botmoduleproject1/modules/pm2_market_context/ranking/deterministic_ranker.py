"""Deterministic cross-sectional ranking (Mode A)."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.pm2 import RankedCandidate, QualificationStateName
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config


_STATE_PRIORITY = {
    QualificationStateName.CONFIRMED: 6,
    QualificationStateName.QUALIFIED: 5,
    QualificationStateName.FORMING: 4,
    QualificationStateName.NEUTRAL: 3,
    QualificationStateName.COOLDOWN: 2,
    QualificationStateName.SUPPRESSED: 1,
    QualificationStateName.INVALIDATED: 0,
    QualificationStateName.STALE: 0,
}


def sort_key(candidate: RankedCandidate) -> tuple:
    card = candidate.scorecard
    return (
        -card.final_confluence_score,
        -card.confidence_score,
        -float(candidate.state.persistence_count),
        -card.directional_edge_gap,
        -card.session_score,
        -card.liquidity_score,
        -_STATE_PRIORITY.get(candidate.state.state, 0),
        candidate.symbol,
    )


class DeterministicRanker:
    def rank(
        self,
        candidates: tuple[RankedCandidate, ...],
        *,
        as_of: datetime,
        config: Pm2Config | None = None,
    ) -> tuple[RankedCandidate, ...]:
        ordered = sorted(candidates, key=sort_key)
        out: list[RankedCandidate] = []
        shortlist_n = config.thresholds.shortlist_size if config is not None else 3
        for index, item in enumerate(ordered, start=1):
            shortlist_rank = index if index <= shortlist_n else None
            out.append(
                item.model_copy(
                    update={
                        "final_rank": index,
                        "shortlist_rank": shortlist_rank,
                        "as_of": as_of,
                    }
                )
            )
        return tuple(out)
