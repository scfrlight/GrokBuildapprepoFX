from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType


@dataclass(frozen=True)
class ExecutionIntake:
    bundle: RiskPublicationBundle | None
    direction: Direction | None
    entry_type: EntryType
    quantity: Decimal | None
    order_type: str
    entry_price: Decimal | None
    stop_price: Decimal | None
    strategy_id: str | None
    cluster: str | None


class ExecutionIntakeService:
    def normalize(
        self,
        bundle: RiskPublicationBundle | None,
        *,
        direction: Direction | None,
        entry_type: EntryType = EntryType.MARKET,
        quantity: Decimal | None = None,
        order_type: str = "market",
        entry_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        strategy_id: str | None = None,
        cluster: str | None = None,
    ) -> ExecutionIntake:
        return ExecutionIntake(
            bundle=bundle,
            direction=direction,
            entry_type=entry_type,
            quantity=quantity,
            order_type=order_type,
            entry_price=entry_price,
            stop_price=stop_price,
            strategy_id=strategy_id,
            cluster=cluster,
        )
