"""Learning-to-rank hook. Sequence 03 does not train a model (not QRF)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from botmoduleproject1.contracts.v1.pm2 import RankedCandidate


@runtime_checkable
class CandidateRanker(Protocol):
    def rank(
        self,
        candidates: tuple[RankedCandidate, ...],
        *,
        as_of: datetime,
    ) -> tuple[RankedCandidate, ...]:
        ...


class LearningToRankHook:
    """Placeholder for a future LambdaMART/XGBoost ranker.

    Consumes feature vectors grouped by scan timestamp. Returns None until a
    research-mode model is wired. Does not estimate returns or replace PM3
    forecasting.
    """

    enabled = False

    def feature_vector(self, candidate: RankedCandidate) -> dict[str, float]:
        card = candidate.scorecard
        return {
            "confluence": card.final_confluence_score,
            "confidence": card.confidence_score,
            "edge": card.directional_edge_gap,
            "regime": card.regime_score,
            "structure": card.structure_score,
            "momentum": card.momentum_score,
            "volatility": card.volatility_score,
            "session": card.session_score,
            "liquidity": card.liquidity_score,
            "correlation_penalty": card.correlation_penalty,
            "persistence": float(candidate.state.persistence_count),
        }

    def rank(
        self,
        candidates: tuple[RankedCandidate, ...],
        *,
        as_of: datetime,
    ) -> tuple[RankedCandidate, ...] | None:
        return None
