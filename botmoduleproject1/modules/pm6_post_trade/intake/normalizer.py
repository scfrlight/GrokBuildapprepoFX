from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from botmoduleproject1.contracts.v1.execution import ExecutionPublicationBundle
from botmoduleproject1.contracts.v1.post_trade import TruthSource
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.modules.pm6_post_trade.intake.pm4_adapter import freeze_or_halt, kill_latched
from botmoduleproject1.modules.pm6_post_trade.intake.pm5_adapter import approved_qty, classify_truth, filled_qty


@dataclass
class NormalizedObserve:
    execution: ExecutionPublicationBundle | None
    risk: RiskPublicationBundle | None
    truth: TruthSource
    kill: bool
    freeze: bool
    approved: object
    filled: object
    symbol: str | None
    now: datetime


def normalize(execution, risk, now: datetime) -> NormalizedObserve:
    return NormalizedObserve(
        execution=execution,
        risk=risk,
        truth=classify_truth(execution),
        kill=kill_latched(risk),
        freeze=freeze_or_halt(risk),
        approved=approved_qty(execution) if execution else None,
        filled=filled_qty(execution) if execution else None,
        symbol=(execution.order.symbol if execution and execution.order else (risk.symbol if risk else None)),
        now=now,
    )
