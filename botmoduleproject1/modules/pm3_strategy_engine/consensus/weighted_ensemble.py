"""Calibrated weighted ensemble. Not majority vote. Not QRF."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.strategy import ConsensusDecision, Direction
from botmoduleproject1.contracts.v1.strategy_engine import (
    StrategyVote,
    SymbolConsensusResult,
    VoteAbstentionReason,
)
from botmoduleproject1.modules.pm3_strategy_engine.config.schema import ConsensusThresholds, ConsensusWeights
from botmoduleproject1.modules.pm3_strategy_engine.consensus.thresholds import vote_weight


def _clip01(value: float) -> float:
    if value != value:  # NaN
        return 0.0
    return min(1.0, max(0.0, float(value)))


class WeightedEnsembleConsensus:
    def __init__(
        self,
        weights: ConsensusWeights | None = None,
        thresholds: ConsensusThresholds | None = None,
    ) -> None:
        self.weights = weights or ConsensusWeights()
        self.thresholds = thresholds or ConsensusThresholds()

    def decide(
        self, votes: tuple[StrategyVote, ...], *, symbol: str, as_of: datetime
    ) -> SymbolConsensusResult:
        selected: list[StrategyVote] = []
        dropped: list[StrategyVote] = []
        for vote in votes:
            if vote.abstained:
                dropped.append(vote)
                continue
            if vote.direction is Direction.FLAT:
                dropped.append(vote)
                continue
            selected.append(vote)

        if len(selected) < self.thresholds.min_selected_votes:
            return SymbolConsensusResult(
                occurred_at=as_of,
                symbol=symbol,
                decision=ConsensusDecision.WAIT,
                p_long=0.0,
                p_short=0.0,
                agreement_score=0.0,
                conflict_score=0.0,
                confidence=0.0,
                selected_votes=tuple(v.vote_id for v in selected),
                dropped_votes=tuple(v.vote_id for v in dropped),
                abstention_reason=VoteAbstentionReason.INSUFFICIENT_EVIDENCE,
                diagnostics={"selected": len(selected), "dropped": len(dropped)},
            )

        long_acc = short_acc = long_w = short_w = 0.0
        details: list[dict[str, float]] = []
        for vote in selected:
            w = vote_weight(
                _clip01(vote.historical_reliability),
                _clip01(vote.regime_fit),
                _clip01(vote.setup_quality),
                _clip01(vote.friction_fit),
                _clip01(vote.recent_live_health),
                self.weights,
            )
            p = _clip01(vote.calibrated_probability)
            details.append({"weight": w, "p": p})
            if vote.direction is Direction.BUY:
                long_acc += w * p
                long_w += w
            elif vote.direction is Direction.SELL:
                short_acc += w * p
                short_w += w

        p_long = (long_acc / long_w) if long_w else 0.0
        p_short = (short_acc / short_w) if short_w else 0.0
        edge = abs(p_long - p_short)
        both = (1 if long_w else 0) + (1 if short_w else 0)
        conflict = min(1.0, (1.0 - edge) * (0.5 if both == 2 else 0.15))
        agreement = min(1.0, edge * (len(selected) / 3.0))
        confidence = min(1.0, max(p_long, p_short) * (1.0 - conflict))

        decision = ConsensusDecision.WAIT
        reason: VoteAbstentionReason | None = VoteAbstentionReason.INSUFFICIENT_EVIDENCE
        if conflict >= self.thresholds.conflict_no_trade and both == 2:
            decision = ConsensusDecision.NO_TRADE
            reason = VoteAbstentionReason.CONSENSUS_NO_TRADE
        elif p_long >= self.thresholds.go_threshold and (p_long - p_short) >= self.thresholds.edge_margin:
            decision = ConsensusDecision.GO_LONG
            reason = None
        elif p_short >= self.thresholds.go_threshold and (p_short - p_long) >= self.thresholds.edge_margin:
            decision = ConsensusDecision.GO_SHORT
            reason = None
        else:
            decision = ConsensusDecision.WAIT
            reason = VoteAbstentionReason.CONSENSUS_WAIT

        return SymbolConsensusResult(
            occurred_at=as_of,
            symbol=symbol,
            decision=decision,
            p_long=p_long,
            p_short=p_short,
            agreement_score=agreement,
            conflict_score=conflict,
            confidence=confidence,
            selected_votes=tuple(v.vote_id for v in selected),
            dropped_votes=tuple(v.vote_id for v in dropped),
            abstention_reason=reason,
            diagnostics={"weights": details, "long_w": long_w, "short_w": short_w},
        )
