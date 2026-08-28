"""Hybrid regime engine: deterministic baseline + optional unused adapters."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.session import RegimeState, RegimeType
from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot
from botmoduleproject1.modules.pm2_market_context.regime.baseline_rules import classify_regime
from botmoduleproject1.modules.pm2_market_context.regime.gmm_adapter import GmmAdapter
from botmoduleproject1.modules.pm2_market_context.regime.hmm_adapter import HmmAdapter
from botmoduleproject1.modules.pm2_market_context.regime.persistence import persist
from botmoduleproject1.modules.pm2_market_context.regime.transitions import transition_label


class RegimeEngine:
    def __init__(self, *, hold: int = 2) -> None:
        self.hold = hold
        self._previous: dict[str, tuple[RegimeType, int]] = {}
        self.hmm = HmmAdapter()
        self.gmm = GmmAdapter()

    def evaluate(self, snapshot: FeatureSnapshot, as_of: datetime) -> tuple[RegimeState, str]:
        incoming, confidence = classify_regime(snapshot)
        prev, seen = self._previous.get(snapshot.symbol, (None, 0))
        chosen, new_seen = persist(prev, incoming, confidence, hold=self.hold, seen=seen)
        self._previous[snapshot.symbol] = (chosen, new_seen)
        label = transition_label(prev, chosen)
        state = RegimeState(
            symbol=snapshot.symbol,
            regime=chosen,
            confidence=confidence,
            as_of=as_of,
            method="deterministic_baseline",
            persistence_bars=new_seen,
        )
        return state, label
