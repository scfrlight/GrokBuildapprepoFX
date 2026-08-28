from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import (
    BrokerAckEvent,
    BrokerEventType,
    FillEvent,
    NormalizedExecutionCommand,
)
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class SimulationBrokerAdapter:
    """Deterministic fake venue. Tickets are SIM-*. Not broker truth."""

    name = "simulation"

    def available(self) -> bool:
        return True

    def submit(self, command: NormalizedExecutionCommand, *, now: datetime) -> list:
        ticket = f"SIM-{command.order_id.hex[:10]}"
        px = command.entry_price or Decimal("0")
        ack = BrokerAckEvent(
            event_id=new_id(),
            order_id=command.order_id,
            occurred_at=now,
            kind=BrokerEventType.SIMULATED_ACK,
            ticket=ticket,
            message="simulation acknowledgement",
        )
        fill = FillEvent(
            fill_id=new_id(),
            order_id=command.order_id,
            occurred_at=now,
            quantity=command.requested_quantity,
            price=px,
            source="simulation",
            ticket=ticket,
        )
        return [ack, fill]

    def cancel(self, command: NormalizedExecutionCommand, *, now: datetime) -> list:
        ticket = f"SIM-{command.order_id.hex[:10]}"
        return [
            BrokerAckEvent(
                event_id=new_id(),
                order_id=command.order_id,
                occurred_at=now,
                kind=BrokerEventType.SIMULATED_CANCEL,
                ticket=ticket,
                message="simulation cancel",
            )
        ]

    def modify(self, command: NormalizedExecutionCommand, *, now: datetime) -> list:
        return self.submit(command, now=now)

    def close(self, command: NormalizedExecutionCommand, *, now: datetime) -> list:
        return self.cancel(command, now=now)

    def fetch_open_orders(self) -> tuple:
        return ()

    def fetch_positions(self) -> tuple:
        return ()

    def health(self) -> dict:
        return {"adapter": self.name, "available": True, "mt5": False, "truth": "simulated"}
