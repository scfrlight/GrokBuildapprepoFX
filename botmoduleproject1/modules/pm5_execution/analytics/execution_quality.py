from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import (
    ExecutionQualityReport,
    FillEvent,
    OrderLifecycleEvent,
    OrderRecord,
)


class ExecutionQualityEngine:
    def report(
        self,
        record: OrderRecord | None,
        events: tuple[OrderLifecycleEvent, ...],
        fills: tuple[FillEvent, ...],
        *,
        now: datetime,
        rejects: int,
        submits: int,
    ) -> ExecutionQualityReport:
        if record is None or not events:
            return ExecutionQualityReport(as_of=now, data_status="insufficient_data", sample_size=0)
        by_state = {e.to_state.value: e.occurred_at for e in events}
        def _ms(a, b) -> Decimal | None:
            if a is None or b is None:
                return None
            return Decimal(str(int((b - a).total_seconds() * 1000)))

        created = events[0].occurred_at
        submitted = by_state.get("submitted")
        ack = by_state.get("acknowledged")
        filled = by_state.get("filled")
        slip: Decimal | None = None
        if fills and record.entry_price is not None:
            slip = fills[-1].price - record.entry_price
        reject_rate = None
        if submits + rejects:
            reject_rate = Decimal(rejects) / Decimal(submits + rejects)
        partial = Decimal("1") if record.state.value == "partially_filled" else Decimal("0")
        success = Decimal("1") if record.state.value in {"filled", "reconciliation_pending"} else Decimal("0")
        return ExecutionQualityReport(
            as_of=now,
            decision_to_submit_ms=_ms(created, submitted),
            submit_to_ack_ms=_ms(submitted, ack),
            ack_to_fill_ms=_ms(ack, filled),
            total_completion_ms=_ms(created, filled or ack or submitted),
            realized_slippage=slip,
            reject_rate=reject_rate,
            partial_fill_ratio=partial,
            success_rate=success,
            sample_size=len(events),
            data_status="ok" if submitted else "insufficient_data",
            dimensions={"symbol": record.symbol, "order_id": str(record.order_id)},
        )
