"""Sequence 11 exit lifecycle. Structural SL/TP, breakeven lock, time stops.

Does not send orders by itself. Emits exit intents for DemoRouter after PM4 ALLOW.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from botmoduleproject1.contracts.v1.time import utc_now


class ExitState(str, Enum):
    ARMED = "armed"
    BREAKEVEN = "breakeven"
    TIME_STOP = "time_stop"
    STRUCTURAL_SL = "structural_sl"
    STRUCTURAL_TP = "structural_tp"
    CLOSED = "closed"


@dataclass
class ExitPlanLive:
    symbol: str
    side: str
    entry: Decimal
    sl: Decimal
    tp: Decimal
    opened_at: datetime
    time_stop_seconds: int = 3600
    breakeven_r: Decimal = Decimal("1")
    state: ExitState = ExitState.ARMED
    events: list[str] = field(default_factory=list)


class ExitEngine:
    def arm(self, *, symbol: str, side: str, entry: Decimal, sl: Decimal, tp: Decimal, now: datetime | None = None) -> ExitPlanLive:
        if sl == entry or tp == entry:
            raise ValueError("structural SL/TP must be away from entry")
        if side == "buy" and not (sl < entry < tp):
            raise ValueError("buy requires sl < entry < tp")
        if side == "sell" and not (tp < entry < sl):
            raise ValueError("sell requires tp < entry < sl")
        return ExitPlanLive(
            symbol=symbol,
            side=side,
            entry=entry,
            sl=sl,
            tp=tp,
            opened_at=now or utc_now(),
        )

    def on_price(self, plan: ExitPlanLive, price: Decimal, *, now: datetime | None = None) -> ExitPlanLive:
        if plan.state is ExitState.CLOSED:
            return plan
        now = now or utc_now()
        if now - plan.opened_at >= timedelta(seconds=plan.time_stop_seconds):
            plan.state = ExitState.TIME_STOP
            plan.events.append("time_stop")
            plan.state = ExitState.CLOSED
            return plan
        r = abs(plan.entry - plan.sl)
        if r > 0:
            move = price - plan.entry if plan.side == "buy" else plan.entry - price
            if move >= r * plan.breakeven_r and plan.state is ExitState.ARMED:
                plan.state = ExitState.BREAKEVEN
                plan.sl = plan.entry
                plan.events.append("breakeven_lock")
        if plan.side == "buy":
            if price <= plan.sl:
                plan.state = ExitState.STRUCTURAL_SL
                plan.events.append("sl")
                plan.state = ExitState.CLOSED
            elif price >= plan.tp:
                plan.state = ExitState.STRUCTURAL_TP
                plan.events.append("tp")
                plan.state = ExitState.CLOSED
        else:
            if price >= plan.sl:
                plan.state = ExitState.STRUCTURAL_SL
                plan.events.append("sl")
                plan.state = ExitState.CLOSED
            elif price <= plan.tp:
                plan.state = ExitState.STRUCTURAL_TP
                plan.events.append("tp")
                plan.state = ExitState.CLOSED
        return plan
