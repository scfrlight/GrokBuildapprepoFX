from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import NormalizedExecutionCommand, OrderRecord
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id
from botmoduleproject1.modules.pm5_execution.intake.validators import approved_quantity


def to_command(
    bundle: RiskPublicationBundle,
    record: OrderRecord,
    *,
    quantity: Decimal,
    order_type: str,
    entry_price: Decimal | None,
    stop_price: Decimal | None,
) -> NormalizedExecutionCommand:
    cap = approved_quantity(bundle)
    return NormalizedExecutionCommand(
        command_id=new_id(),
        order_id=record.order_id,
        pm4_decision_id=bundle.verdict.verdict_id,
        symbol=record.symbol,
        direction=record.direction,
        approved_quantity=cap,
        requested_quantity=quantity,
        order_type=order_type,
        entry_price=entry_price,
        stop_price=stop_price,
        execution_policy="simulation_only",
        route_restrictions=("broker_closed",),
        idempotency_key=record.idempotency_key,
        correlation_id=record.correlation_id,
        causation_id=record.causation_id,
        broker_eligible=False,
    )
