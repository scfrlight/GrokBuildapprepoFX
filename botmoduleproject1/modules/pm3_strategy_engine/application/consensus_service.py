from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.strategy_engine import StrategyVote, SymbolConsensusResult
from botmoduleproject1.modules.pm3_strategy_engine.config.schema import ConsensusThresholds, ConsensusWeights
from botmoduleproject1.modules.pm3_strategy_engine.consensus.weighted_ensemble import WeightedEnsembleConsensus


class ConsensusService:
    def __init__(
        self,
        weights: ConsensusWeights | None = None,
        thresholds: ConsensusThresholds | None = None,
    ) -> None:
        self.engine = WeightedEnsembleConsensus(weights=weights, thresholds=thresholds)

    def decide(
        self, votes: tuple[StrategyVote, ...], *, symbol: str, as_of: datetime
    ) -> SymbolConsensusResult:
        return self.engine.decide(votes, symbol=symbol, as_of=as_of)
