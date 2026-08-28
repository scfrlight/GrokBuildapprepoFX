"""Account-level pass-through. No risk or sizing."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import (
    ExecutionContext,
    PortfolioContext,
    RiskContext,
    SystemFlags,
)


class GlobalSystemPipe:
    def __init__(self, flags: SystemFlags | None = None) -> None:
        self.flags = flags or SystemFlags()

    def context(self, as_of: datetime) -> dict:
        return {
            "flags": self.flags,
            "portfolio": PortfolioContext(as_of=as_of),
            "risk": RiskContext(as_of=as_of),
            "execution": ExecutionContext(as_of=as_of),
        }

    def evaluation_permitted(self) -> bool:
        if self.flags.live_trading:
            return False
        return self.flags.strategy_evaluation_enabled
