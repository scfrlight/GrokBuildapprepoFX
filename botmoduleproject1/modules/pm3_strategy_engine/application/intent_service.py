from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from botmoduleproject1.contracts.v1.pm2 import RankedCandidate
from botmoduleproject1.contracts.v1.strategy import (
    ConsensusDecision,
    Direction,
    EntryType,
    ExitPlan,
    NoTradeDecision,
    StopType,
    TradeIntent,
    UrgencyClass,
)
from botmoduleproject1.contracts.v1.strategy_engine import SymbolConsensusResult, VoteAbstentionReason
from botmoduleproject1.modules.pm3_strategy_engine.domain.factories import no_trade


def _intent_key(symbol: str, as_of: datetime, candidate_id) -> str:
    return f"pm3se:{symbol}:{as_of.isoformat()}:{candidate_id}"


class IntentService:
    def __init__(self, expiry_hours: int = 4) -> None:
        self.expiry_hours = expiry_hours

    def from_consensus(
        self,
        consensus: SymbolConsensusResult,
        candidate: RankedCandidate,
        *,
        profile_id: str | None,
        version_id: str | None,
    ) -> TradeIntent | NoTradeDecision:
        as_of = candidate.as_of
        if consensus.decision in {ConsensusDecision.WAIT, ConsensusDecision.ABSTAIN}:
            return no_trade(
                candidate.symbol,
                as_of,
                "consensus_wait",
                correlation_id=candidate.correlation_id,
                diagnostics={"decision": consensus.decision.value},
            )
        if consensus.decision in {ConsensusDecision.NO_TRADE, ConsensusDecision.REJECT}:
            return no_trade(
                candidate.symbol,
                as_of,
                "consensus_no_trade",
                correlation_id=candidate.correlation_id,
                diagnostics={"conflict": consensus.conflict_score},
            )
        if consensus.decision is ConsensusDecision.GO_LONG:
            direction = Direction.BUY
        elif consensus.decision is ConsensusDecision.GO_SHORT:
            direction = Direction.SELL
        else:
            return no_trade(
                candidate.symbol,
                as_of,
                "consensus_not_directional",
                correlation_id=candidate.correlation_id,
            )
        close_hint = Decimal("1")
        zone = Decimal("0.0004")
        exit_plan = ExitPlan(
            stop_type=StopType.ATR,
            stop_price=None,
            tp_plan="1R/2R ladder (analytical)",
            trail_plan="none",
            time_stop_plan=f"{self.expiry_hours}h",
            time_stop_seconds=self.expiry_hours * 3600,
            notes="analytical exit sketch; PM4/PM5 not invoked",
        )
        return TradeIntent(
            correlation_id=candidate.correlation_id,
            causation_id=candidate.event_id,
            idempotency_key=_intent_key(candidate.symbol, as_of, candidate.candidate_id),
            occurred_at=as_of,
            created_at=as_of,
            symbol=candidate.symbol,
            direction=direction,
            entry_type=EntryType.LIMIT,
            requested_volume=None,
            exit_plan=exit_plan,
            consensus=consensus.decision,
            thesis="PM3-Strategy Engine calibrated consensus (observe-only)",
            profile_id=profile_id,
            version_id=version_id,
            entry_zone_low=close_hint - zone,
            entry_zone_high=close_hint + zone,
            confidence_score=consensus.confidence,
            setup_quality=min(1.0, candidate.scorecard.final_confluence_score / 100.0),
            consensus_score=max(consensus.p_long, consensus.p_short),
            regime_state=candidate.context.regime.value,
            urgency_class=UrgencyClass.NORMAL,
            signal_expiry=as_of + timedelta(hours=self.expiry_hours),
            diagnostics={
                "p_long": consensus.p_long,
                "p_short": consensus.p_short,
                "observe_only": True,
                "not_an_order": True,
            },
            source_candidate_id=candidate.candidate_id,
            pm2_rank=candidate.final_rank,
        )
