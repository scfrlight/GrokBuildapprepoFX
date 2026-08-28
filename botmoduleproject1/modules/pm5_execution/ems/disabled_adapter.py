from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.execution import BrokerAckEvent, BrokerEventType, NormalizedExecutionCommand
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class DisabledBrokerAdapter:
    name = "disabled"

    def available(self) -> bool:
        return False

    def submit(self, command: NormalizedExecutionCommand, *, now: datetime) -> list[BrokerAckEvent]:
        return [
            BrokerAckEvent(
                event_id=new_id(),
                order_id=command.order_id,
                occurred_at=now,
                kind=BrokerEventType.DISABLED,
                message="DisabledBrokerAdapter: no side effect, no MT5, no ticket",
            )
        ]

    def cancel(self, command: NormalizedExecutionCommand, *, now: datetime) -> list[BrokerAckEvent]:
        return self.submit(command, now=now)

    def modify(self, command: NormalizedExecutionCommand, *, now: datetime) -> list[BrokerAckEvent]:
        return self.submit(command, now=now)

    def close(self, command: NormalizedExecutionCommand, *, now: datetime) -> list[BrokerAckEvent]:
        return self.submit(command, now=now)

    def fetch_open_orders(self) -> tuple:
        return ()

    def fetch_positions(self) -> tuple:
        return ()

    def health(self) -> dict:
        return {"adapter": self.name, "available": False, "mt5": False}
