from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.execution import (
    ExecutionIntentReceipt,
    ExecutionMode,
    ExecutionPublicationBundle,
    ExecutionQualityReport,
    ExposureState,
    FillEvent,
    NormalizedExecutionCommand,
    OrderRecord,
    Pm5OperatingState,
    ReconciliationRecord,
)
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class ExecutionPublicationService:
    def build(
        self,
        *,
        now: datetime,
        receipt: ExecutionIntentReceipt,
        order: OrderRecord | None,
        command: NormalizedExecutionCommand | None,
        lifecycle,
        fills: tuple[FillEvent, ...],
        control,
        recon: ReconciliationRecord | None,
        exposure: ExposureState | None,
        quality: ExecutionQualityReport | None,
        alerts,
        operating: Pm5OperatingState,
        mode: ExecutionMode,
    ) -> ExecutionPublicationBundle:
        return ExecutionPublicationBundle(
            bundle_id=new_id(),
            occurred_at=now,
            order=order,
            receipt=receipt,
            command=command,
            lifecycle=tuple(lifecycle),
            fills=fills,
            control=tuple(control),
            reconciliation=recon,
            exposure=exposure,
            quality=quality,
            alerts=tuple(alerts),
            operating_state=operating,
            execution_mode=mode,
            broker_side_effect=False,
            mt5_used=False,
            durable=False,
            producer="pm5_execution",
        )
