from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy_engine import StrategyVote
from botmoduleproject1.modules.pm3_strategy_engine.consensus.calibration import policy_for


class CalibrationService:
    def __init__(self, policy_name: str = "reliability_table") -> None:
        self.policy = policy_for(policy_name)

    def apply(self, vote: StrategyVote) -> StrategyVote:
        return self.policy.calibrate(vote)
