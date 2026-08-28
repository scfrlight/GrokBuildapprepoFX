from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import (
    ExecutionLifecycleState,
    ExposureState,
    OrderRecord,
    ReconciliationOutcome,
    ReconciliationRecord,
)

_WORKING = {
    ExecutionLifecycleState.QUEUED,
    ExecutionLifecycleState.SUBMITTED,
    ExecutionLifecycleState.ACKNOWLEDGED,
    ExecutionLifecycleState.PARTIALLY_FILLED,
    ExecutionLifecycleState.CANCEL_REQUESTED,
    ExecutionLifecycleState.MODIFY_REQUESTED,
    ExecutionLifecycleState.RECONCILIATION_PENDING,
}


class ExposureTruthService:
    def snapshot(
        self,
        orders: tuple[OrderRecord, ...],
        *,
        now: datetime,
        recon: ReconciliationRecord | None,
    ) -> ExposureState:
        working = [o for o in orders if o.state in _WORKING]
        positions = [o for o in orders if o.filled_quantity > 0]
        working_qty = sum((o.remaining_quantity for o in working), Decimal("0"))
        pos_qty = sum((o.filled_quantity for o in positions), Decimal("0"))
        remaining = sum((o.remaining_quantity for o in orders), Decimal("0"))
        expected = working_qty + pos_qty
        outcome = recon.outcome if recon else ReconciliationOutcome.DEGRADED
        return ExposureState(
            as_of=now,
            working_orders=len(working),
            open_positions=len(positions),
            working_quantity=working_qty,
            position_quantity=pos_qty,
            remaining_quantity=remaining,
            expected_exposure=expected,
            broker_exposure=None,
            exposure_delta=None,
            reconciliation_status=outcome,
            last_broker_refresh=None,
            stale=True,
            broker_truth_available=False,
        )
