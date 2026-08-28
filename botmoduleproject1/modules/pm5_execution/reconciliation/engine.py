from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.execution import ReconciliationOutcome, ReconciliationRecord
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class ReconciliationEngine:
    def run(
        self,
        *,
        now: datetime,
        local_order_count: int,
        broker_order_count: int | None,
        broker_truth_available: bool,
        fill_mismatch: bool = False,
        position_mismatch: bool = False,
        missing_broker_order: bool = False,
        unexpected_broker_order: bool = False,
    ) -> ReconciliationRecord:
        if not broker_truth_available:
            return ReconciliationRecord(
                record_id=new_id(),
                as_of=now,
                consistent=False,
                ledger_position_count=local_order_count,
                broker_position_count=broker_order_count or 0,
                notes="broker truth unavailable; simulation is not a venue",
                outcome=ReconciliationOutcome.DEGRADED,
                mismatch_type="broker_truth_unavailable",
                severity="medium",
                local_state={"orders": local_order_count},
                broker_state={"available": False},
                recommended_action="do_not_submit_to_broker",
                remediation_status="accepted_limitation",
                broker_truth_available=False,
            )
        if fill_mismatch or position_mismatch or missing_broker_order or unexpected_broker_order:
            critical = position_mismatch or missing_broker_order
            return ReconciliationRecord(
                record_id=new_id(),
                as_of=now,
                consistent=False,
                ledger_position_count=local_order_count,
                broker_position_count=broker_order_count or 0,
                notes="mismatch versus broker truth",
                outcome=ReconciliationOutcome.CRITICAL if critical else ReconciliationOutcome.MISMATCH,
                mismatch_type="state_delta",
                severity="critical" if critical else "high",
                recommended_action="block_new_orders_and_recover",
                remediation_status="open",
                broker_truth_available=True,
            )
        return ReconciliationRecord(
            record_id=new_id(),
            as_of=now,
            consistent=True,
            ledger_position_count=local_order_count,
            broker_position_count=broker_order_count or 0,
            notes="local equals broker",
            outcome=ReconciliationOutcome.PASS,
            recommended_action="none",
            remediation_status="cleared",
            broker_truth_available=True,
        )
